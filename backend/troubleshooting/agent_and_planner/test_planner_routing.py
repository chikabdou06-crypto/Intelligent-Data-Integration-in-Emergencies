import sys
from pathlib import Path

# Add project root to path (4 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.planner import discover_skills, select_relevant_skills

def main():
    print("=" * 60)
    print("Testing Planner Skill Routing")
    print("=" * 60)

    # 1. Discover all skills
    all_skills = discover_skills()
    print(f"\nDiscovered {len(all_skills)} skill(s):")
    for s in all_skills:
        print(f"  - Name: {s['name']} | Folder: {s['folder_name']}")
        print(f"    Description: {s['description'][:80]}...")

    # 2. Test prompt matching
    test_prompts = [
        "What files exist in our cloud drive?",
        "Lookup unemployment in the paro CSV dataset and aggregate the sum",
        "Explain how the attendance policy is structured",
        "Add a connection node in Neo4j graph"
    ]

    for p in test_prompts:
        print(f"\nPrompt: \"{p}\"")
        matched = select_relevant_skills(p, all_skills)
        print(f"  Matched {len(matched)} skill(s):")
        for m in matched:
            print(f"    -> {m['name']}")

if __name__ == "__main__":
    main()
