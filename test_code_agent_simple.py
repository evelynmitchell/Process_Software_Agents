"""
Simple test for Code Agent with mocked LLM response.
"""
import json
from unittest.mock import patch, MagicMock
from asp.agents.code_agent import CodeAgent
from asp.models.code import CodeInput
from asp.models.design import DesignSpecification

print("Loading design from bootstrap artifacts...")
with open('artifacts/BOOTSTRAP-001/design.json', 'r') as f:
    design_data = json.load(f)

design = DesignSpecification(**design_data)

# Create code input
code_input = CodeInput(
    task_id=design.task_id,
    design_specification=design
)

# Mock LLM response (wrapped in markdown fence to test our fix)
mock_llm_response = {
    "content": '''```json
{
  "task_id": "BOOTSTRAP-001",
  "project_id": "ASP-CORE",
  "files": [
    {
      "file_path": "src/api/health.py",
      "content": "# Health check endpoint\\nfrom fastapi import APIRouter\\n\\nrouter = APIRouter()\\n\\n@router.get('/health')\\ndef health():\\n    return {'status': 'ok'}",
      "file_type": "source",
      "semantic_unit_id": "SU-001",
      "component_id": "COMP-001",
      "description": "Health check API endpoint"
    }
  ],
  "file_structure": {
    "src/api": ["health.py"]
  },
  "implementation_notes": "Simple health check endpoint using FastAPI router. Returns status OK for basic health monitoring.",
  "total_files": 1,
  "total_lines_of_code": 8,
  "generation_timestamp": "2025-11-18T12:00:00"
}
```''',
    "usage": {"input_tokens": 100, "output_tokens": 200}
}

print("Testing Code Agent with mocked LLM...")
print("=" * 80)

try:
    agent = CodeAgent()

    # Mock the call_llm method to return our test response instantly
    with patch.object(agent, 'call_llm', return_value=mock_llm_response):
        print("Calling Code Agent execute()...")
        result = agent.execute(code_input)

        print(f"✅ Code Agent execution successful!")
        print(f"   Task ID: {result.task_id}")
        print(f"   Files generated: {len(result.files)}")
        print(f"   Total LOC: {result.total_lines_of_code}")

        for file in result.files:
            print(f"\n   File: {file.file_path}")
            print(f"   Type: {file.file_type}")
            print(f"   Component: {file.component_id}")

except Exception as e:
    print(f"❌ Code Agent failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete!")
