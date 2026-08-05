import re
import json
from pathlib import Path
from backend.core.llm import LLMClient
from backend.core.prompts import get_planner_prompt

# Path to the skills directory
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def _parse_skill_frontmatter(raw: str) -> tuple[str, str, str]:
    """
    Parses a SKILL.md raw string.
    Returns (name, description, body) where body has frontmatter stripped.
    """
    name = ""
    description = ""
    body = raw

    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            frontmatter = raw[3:end]
            body = raw[end + 3:].strip()
            for line in frontmatter.splitlines():
                if line.startswith("name:"):
                    name = line[5:].strip()
                elif line.startswith("description:"):
                    description = line[12:].strip()

    return name, description, body


def discover_skills() -> list:
    """
    Scans backend/skills/ and returns a list of skill dicts.
    Each dict has: name, description, body, folder_name.
    This is cheap — just reads frontmatter for all skills.
    """
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_path in sorted(SKILLS_DIR.glob("*.md")):
        try:
            raw = skill_path.read_text(encoding="utf-8").strip()
            name, description, body = _parse_skill_frontmatter(raw)
            skills.append({
                "folder_name": skill_path.stem,
                "name": name or skill_path.stem,
                "description": description,
                "body": body,
            })
        except Exception as e:
            print(f"[Planner] Warning: could not read skill {skill_path}: {e}")

    return skills


def select_relevant_skills(prompt: str, all_skills: list) -> list:
    """
    Selects skills relevant to the prompt using keyword matching.
    Reads the skill description to derive keywords dynamically.
    Injects full body only for matched ones.
    """
    prompt_lower = prompt.lower()
    selected = []

    for skill in all_skills:
        # Dynamically extract words from the description
        keywords = []
        if skill["description"]:
            # Basic tokenization of the description
            keywords = [w.lower() for w in re.findall(r'\b\w+\b', skill["description"]) if len(w) > 3]

        matched = any(kw in prompt_lower for kw in keywords)

        if matched:
            selected.append(skill)
            print(f"[Planner] Skill activated: '{skill['name']}'")

    if not selected:
        print("[Planner] No skills matched. Proceeding without skill injection.")

    return selected


def generate_plan(prompt: str, conversation_history: str = "") -> list:
    """
    Two-phase planning with Progressive Skill Disclosure:

      Phase 1 — Skill Routing:
        Discovers all skills (reads frontmatter only).
        Selects relevant ones via keyword matching against the user prompt.
        No extra LLM call needed.

      Phase 2 — Plan Generation:
        Injects ONLY the full bodies of selected skills into the LLM prompt.
        Calls the LLM once to generate the execution plan.
    """
    # ── Phase 1: Skill Routing ─────────────────────────────────────────────
    all_skills = discover_skills()
    selected_skills = select_relevant_skills(prompt, all_skills)

    if selected_skills:
        skill_blocks = [
            f"=== SKILL: {s['name']} ===\n{s['body']}"
            for s in selected_skills
        ]
        skills_section = (
            "\n========== AGENT SKILLS (Follow These Instructions) ==========\n"
            + "\n\n".join(skill_blocks)
            + "\n"
        )
        print(f"[Planner] Injecting {len(selected_skills)} skill(s): "
              f"{[s['name'] for s in selected_skills]}")
    else:
        skills_section = ""

    # ── Phase 2: Build Tool Menu ───────────────────────────────────────────
    # ── Phase 2: Build Tool Menu (via MCP) ────────────────────────────────
    from backend.mcp_core.mcp_client import get_mcp_client
    
    tool_lines = []
    try:
        mcp = get_mcp_client()
        mcp_tools = mcp.get_tools()
        
        for tool in mcp_tools.tools:
            try:
                schema = tool.inputSchema or {}
                params = schema.get("properties", {})
                required = schema.get("required", [])

                param_names = list(params.keys())
                param_str = f"({', '.join(param_names)})"
                desc = " ".join((tool.description or "").strip().split())
                if len(desc) > 120:
                    desc = desc[:117] + "..."
                tool_lines.append(f'- "{tool.name}": {desc} Params: {param_str}')
            except Exception as e:
                print(f"[Warning] Skipping {tool.name} in planner: {e}")
                continue
    except Exception as e:
        print(f"[Error] Failed to fetch tools from MCP server: {e}")

    tools_text = "\n".join(tool_lines)

    try:
        mcp_result = mcp.call_tool("vault_catalog", {})
        raw_text = mcp_result.content[0].text
        catalog_str = json.dumps(json.loads(raw_text), indent=2)
    except Exception as e:
        catalog_str = f"Error loading vault catalog via MCP: {e}"

    # ── Phase 2: Assemble & Call LLM ──────────────────────────────────────
    system_msg = get_planner_prompt(catalog_str, skills_section, tools_text)

    # Inject conversation history if available
    history_block = ""
    if conversation_history:
        history_block = f"\n{conversation_history}\n"
        print(f"[Planner] Injecting conversation history ({len(conversation_history)} chars)")

    llm = LLMClient(role="planner", temperature=0.1)
    result = llm.generate_json(
        system_msg + history_block + f"\n\nUser Prompt: \"{prompt}\"\nJSON Response:"
    )

    steps = result.get("steps", [])
    if not steps:
        print("[Planner] Failed to generate steps or returned empty plan.")
        steps = [{"tool": "general", "arguments": {}}]

    return steps[:6]  # Enforce max 6 steps
