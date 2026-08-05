import json
import os

artifact_path = r"C:\Users\PCSTAR\.gemini\antigravity-ide\brain\06235d2a-416f-48f7-bd31-2f5fdf268cc7\e2e_test_results.md"
json_path = r"c:\Users\PCSTAR\Desktop\TFM\RAG_BASIC_TEST_LANGCHAIN\e2e_results.json"

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

markdown = "# End-to-End LLM Agent Tests\n\n"
for i, test in enumerate(data):
    markdown += f"## Test {i+1}\n"
    markdown += f"**Question:** `{test['question']}`\n\n"
    
    markdown += "### Executed Plan Trace\n"
    for step in test['execution_trace']:
        markdown += f"- **Tool**: `{step['tool']}`\n"
        markdown += f"  - **Arguments**: `{json.dumps(step['arguments'])}`\n"
        res_status = step['result'].get('status', 'unknown')
        if res_status == "error":
            markdown += f"  - **Result**: ❌ ERROR - {step['result'].get('error_message')}\n"
        else:
            rows = step['result'].get('total_rows', step['result'].get('active_warnings_count', 'N/A'))
            markdown += f"  - **Result**: ✅ SUCCESS ({rows} items retrieved)\n"
    
    markdown += "\n### Final Synthesized Answer from LLM\n"
    markdown += f"{test.get('final_answer', 'None')}\n\n"
    markdown += "---\n\n"

with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write(markdown)
