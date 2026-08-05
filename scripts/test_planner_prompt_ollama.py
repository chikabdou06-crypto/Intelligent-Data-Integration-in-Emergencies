import requests
from backend.core.planner import discover_skills, select_relevant_skills
from backend.core.prompts import get_planner_prompt
from backend.core.registry import list_all_tools, get_tool

tools_lines = []
for t in list_all_tools():
    try:
        tool = get_tool(t)
        params = list((tool.inputSchema or {}).get("properties", {}).keys()) if hasattr(tool, 'inputSchema') else list((tool.get_schema() or {}).get("parameters", {}).get("properties", {}).keys())
        param_str = f"({', '.join(params)})"
        desc = " ".join((tool.description or "").strip().split())
        if len(desc) > 120:
            desc = desc[:117] + "..."
        tools_lines.append(f'- "{tool.name}": {desc} Params: {param_str}')
    except Exception:
        pass
tools_text = '\n'.join(tools_lines)
prompt = get_planner_prompt('{}', '', tools_text) + '\nUser Prompt: What is 2+2?'
print('Prompt length:', len(prompt))

import time

t0 = time.time()
try:
    r = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'qwen2.5:7b',
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.1,
                'num_ctx': 8192
            }
        },
        timeout=600
    )
    print(f'Completed in {time.time()-t0:.1f}s - Status: {r.status_code}')
    print('Response:', r.text[:300])
except Exception as e:
    print(f'FAILED after {time.time()-t0:.1f}s:', e)
