"""
Test the JSON parsing fix in Code Agent.
"""
import re
import json

# Simulate the problematic LLM response (JSON wrapped in markdown)
llm_response_with_fence = '''```json
{
  "task_id": "TEST-001",
  "project_id": "TEST",
  "files": [
    {
      "file_path": "test.py",
      "content": "print('hello')",
      "file_type": "source",
      "semantic_unit_id": "SU-001",
      "component_id": "COMP-001",
      "description": "Test file"
    }
  ],
  "total_files": 1,
  "total_lines_of_code": 1,
  "generation_timestamp": "2025-11-18T12:00:00"
}
```'''

print("Testing JSON extraction from markdown fence...")
print("=" * 80)
print(f"Input type: {type(llm_response_with_fence)}")
print(f"Input length: {len(llm_response_with_fence)} chars")
print()

# This is the fix we added to Code Agent
content = llm_response_with_fence

if isinstance(content, str):
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        try:
            content = json.loads(json_match.group(1))
            print("✅ Successfully extracted JSON from markdown code fence")
            print(f"   Extracted type: {type(content)}")
            print(f"   Keys: {list(content.keys())}")
            print(f"   Files: {len(content.get('files', []))}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
    else:
        print("❌ No markdown fence found")
else:
    print(f"❌ Content is not a string: {type(content)}")

print()
print("Testing complete!")
