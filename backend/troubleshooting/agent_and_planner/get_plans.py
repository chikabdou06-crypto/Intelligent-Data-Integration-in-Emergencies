import json

log_path = r"C:\Users\PCSTAR\.gemini\antigravity-ide\brain\d12e8ca5-097a-406b-92a5-b31b871e588c\.system_generated\logs\transcript.jsonl"

plans = []
try:
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if 'tool_calls' in data:
                    for call in data['tool_calls']:
                        name = call.get('name') or call.get('function', {}).get('name')
                        if name in ('default_api:write_to_file', 'write_to_file'):
                            args = call.get('arguments') or call.get('function', {}).get('arguments')
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except:
                                    pass
                            
                            if isinstance(args, dict):
                                if args.get('IsArtifact') and 'implementation_plan' in str(args.get('TargetFile', '')):
                                    plans.append(args.get('CodeContent', ''))
                                elif args.get('ArtifactMetadata', {}).get('ArtifactType') == 'implementation_plan':
                                    plans.append(args.get('CodeContent', ''))
            except Exception as e:
                pass
except Exception as e:
    print(f"Error reading log: {e}")

if not plans:
    print("No plans found in the log.")

for i, plan in enumerate(plans):
    print(f"=== Plan {i+1} ===")
    print(plan)
    print("=" * 40)
