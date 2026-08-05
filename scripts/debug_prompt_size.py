import json
from backend.core.registry import list_all_tools, get_tool
from backend.core.planner import discover_skills, select_relevant_skills

tool_lines = []
for tool_name in list_all_tools():
    try:
        tool = get_tool(tool_name)
        schema = tool.get_schema()
        params = list(schema.get("parameters", {}).get("properties", {}).keys())
        param_str = f"({', '.join(params)})"
        desc = " ".join((tool.description or "").strip().split())
        if len(desc) > 120:
            desc = desc[:117] + "..."
        tool_lines.append(f'- "{tool.name}": {desc} Params: {param_str}')
    except Exception as e:
        pass

tools_text = "\n".join(tool_lines)
print("Tools menu len:", len(tools_text))

skills = discover_skills()
print("Skills count:", len(skills))
