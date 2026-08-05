from backend.core.cache import get_cached_result, set_cached_result
from backend.mcp_core.mcp_client import get_mcp_client
from backend.core.llm import LLMClient
import json

class DependencyError(Exception):
    pass

def _invoke_llm_judge(tool_name: str, failed_args: dict, error_message: str, prior_steps: list) -> dict:
    """Asks the LLM to fix the arguments for a tool that just crashed due to a schema/type error."""
    print(f"\n[LLM Judge] Intercepted crash for '{tool_name}'. Requesting self-correction...")
    
    prompt = f"""You are the LLM Judge. The planner just tried to execute the tool '{tool_name}' but it crashed due to a strict validation/schema error.
    
    Tool: {tool_name}
    Arguments provided: {json.dumps(failed_args)}
    Error encountered: {error_message}
    
    Your task is to fix the arguments so they strictly conform to the expected format/type and resolve the error. 
    Only output a valid JSON object containing the corrected arguments. Do NOT use markdown code blocks, just raw JSON.
    """
    llm = LLMClient(role="planner", temperature=0.0)
    try:
        fixed_args = llm.generate_json(prompt)
        print(f"[LLM Judge] Correction generated: {fixed_args}")
        return fixed_args
    except Exception as e:
        print(f"[LLM Judge] Failed to generate correction: {e}")
        return failed_args


def _deep_get(obj, path: str):
    """Navigate a nested dict/list with dot-separated keys, e.g. 'data.0.postal'."""
    for part in path.split("."):
        if obj is None:
            return None
        if isinstance(obj, list):
            try:
                obj = obj[int(part)]
            except (IndexError, ValueError):
                return None
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj

def _resolve_placeholder(value, prior: list):
    """Resolve a placeholder string like '$PREV.data.0.postal'."""
    if not isinstance(value, str) or not value.startswith("$"):
        return value

    token = value[1:]  # strip leading $
    if token.startswith("PREV."):
        path = token[5:]  # strip 'PREV.'
        if not prior:
            print(f"[Orchestrator] Warning: Cannot resolve '{value}' because there are no prior steps.")
            return None
        
        # Smart Backwards Search: Look through all previous steps starting from the most recent
        for step_idx in range(len(prior) - 1, -1, -1):
            step_result = prior[step_idx].get("result") or {}
            
            # Skip steps that resulted in an error during backward search
            if isinstance(step_result, dict) and step_result.get("status") == "error":
                continue
            
            val = _deep_get(step_result, path)
            if val is not None:
                return val
        
        # If we get here, either all steps failed or the path wasn't found.
        # Check if the *immediate* previous step failed to give a helpful error.
        immediate_prev = prior[-1].get("result") or {} if prior else {}
        if isinstance(immediate_prev, dict) and immediate_prev.get("status") == "error":
            raise DependencyError(f"Previous step failed, cannot resolve '{value}'")
            
        print(f"[Orchestrator] Warning: Failed to resolve placeholder '{value}' from prior steps. Path '{path}' not found.")
        return None
        
    if token.startswith("STEP_"):
        rest = token[5:]  # strip 'STEP_'
        idx_str, _, path = rest.partition(".")
        try:
            idx = int(idx_str)
        except ValueError:
            return value
        if 0 <= idx < len(prior):
            step_result = prior[idx].get("result") or {}
            if isinstance(step_result, dict) and step_result.get("status") == "error":
                raise DependencyError(f"Step {idx} failed, cannot resolve '{value}'")
                
            return _deep_get(step_result, path)
            
    return value

def _enrich_args_from_prior(arguments: dict, prior: list) -> dict:
    """Substitutes placeholders with actual values from prior step results."""
    args = dict(arguments or {})
    for key, val in list(args.items()):
        resolved = _resolve_placeholder(val, prior)
        if resolved is not None and resolved != val:
            args[key] = resolved
    return args

def execute_plan(steps: list) -> list:
    """
    Runs a sequential list of steps (the execution plan).
    Handles caching and cross-step dependency resolution.
    """
    executed = []
    
    for step in steps:
        tool_name = step.get("tool", "general")
        args = step.get("arguments", {})
        
        try:
            # 1. Resolve Dependencies
            resolved_args = _enrich_args_from_prior(args, executed)
            
            if tool_name == "general":
                executed.append({"tool": tool_name, "arguments": resolved_args, "result": None})
                continue
            # 2. Get MCP Client
            mcp = get_mcp_client()
            
            # 3. Check Cache
            # We assume caching by default via MCP, with a generic 6-hour TTL
            # Certain tools might need bypasses, but generically we apply it.
            should_use_cache = tool_name not in ["general", "mcp_server"]
            
            if should_use_cache:
                cached = get_cached_result(tool_name, resolved_args, ttl_hours=6)
                if cached is not None:
                    print(f"  [Step] {tool_name}({resolved_args}) -> CACHED")
                    executed.append({"tool": tool_name, "arguments": resolved_args, "result": cached, "cached": True})
                    continue
                
            # 4. Execute Tool via MCP (with LLM Judge Reflection Loop)
            max_retries = 1
            result = None
            for attempt in range(max_retries + 1):
                print(f"  [Step] MCP -> {tool_name}({resolved_args})")
                try:
                    mcp_result = mcp.call_tool(tool_name, resolved_args)
                    
                    # Parse MCP response
                    try:
                        raw_text = mcp_result.content[0].text
                        result = json.loads(raw_text)
                    except Exception as e:
                        result = {
                            "status": "error",
                            "source": "mcp_client",
                            "error_message": f"Failed to parse MCP response: {e}",
                            "raw_response": str(mcp_result)
                        }
                except Exception as e:
                    # MCP tool invocation crashed (e.g., Pydantic schema validation error)
                    result = {
                        "status": "error",
                        "source": "mcp_sdk",
                        "error_message": str(e)
                    }
                
                if isinstance(result, dict) and result.get("status") == "error":
                    if attempt < max_retries:
                        error_msg = result.get("error_message") or result.get("message", "Unknown error")
                        print(f"         -> status=error: {error_msg[:150]}")
                        
                        # Invoke Judge
                        fixed_args = _invoke_llm_judge(tool_name, resolved_args, error_msg, executed)
                        if fixed_args and isinstance(fixed_args, dict):
                            # The LLM judge might output {"arguments": {...}} or just {...}
                            resolved_args = fixed_args.get("arguments", fixed_args)
                            continue # Try again with fixed args
                
                # If we get here, it either succeeded or we exhausted retries
                break
            
            # Log a summary of the result
            if isinstance(result, dict):
                status = result.get("status", "ok")
                total = result.get("total_rows", result.get("count", "?"))
                msg = result.get("message") or result.get("error_message") or ""
                print(f"         -> status={status}, rows={total} {msg[:100]}")
            else:
                print(f"         -> {str(result)[:150]}")
            
            # 5. Save Cache
            if should_use_cache and isinstance(result, dict) and result.get("status") != "error":
                set_cached_result(tool_name, resolved_args, result)
            
            executed.append({"tool": tool_name, "arguments": resolved_args, "result": result, "cached": False})
            
        except DependencyError as e:
            print(f"  [Step] {tool_name} -> SKIPPED (Dependency Failed): {e}")
            executed.append({
                "tool": tool_name, 
                "arguments": args, 
                "result": {
                    "status": "error",
                    "source": "orchestrator",
                    "error_message": f"Skipped due to dependency failure: {e}",
                    "data": {},
                    "metadata": {}
                }, 
                "error": True,
                "skipped": True
            })
            
        except Exception as e:
            print(f"  [Step] {tool_name} -> ERROR: {e}")
            executed.append({
                "tool": tool_name, 
                "arguments": args, 
                "result": {
                    "status": "error",
                    "source": tool_name,
                    "error_message": str(e),
                    "data": {},
                    "metadata": {}
                }, 
                "error": True
            })
            
    return executed
