"""
Minimal test for Code Agent JSON parsing fix.
"""
import json
from asp.agents.code_agent import CodeAgent
from asp.models.code import CodeInput
from asp.models.design import DesignSpecification

# Load actual design from bootstrap artifacts
with open('artifacts/BOOTSTRAP-001/design.json', 'r') as f:
    design_data = json.load(f)

design = DesignSpecification(**design_data)

# Create code input
code_input = CodeInput(
    task_id=design.task_id,
    design_specification=design
)

# Test Code Agent
print("Testing Code Agent...")
print("=" * 80)

try:
    agent = CodeAgent()
    result = agent.execute(code_input)

    print(f"✅ Code generation successful!")
    print(f"   Files generated: {len(result.files)}")
    print(f"   Total LOC: {result.total_lines_of_code}")

    for file in result.files[:3]:  # Show first 3 files
        print(f"\n   File: {file.file_path}")
        print(f"   Type: {file.file_type}")
        print(f"   Lines: {len(file.content.split(chr(10)))}")

except Exception as e:
    print(f"❌ Code generation failed: {e}")
    import traceback
    traceback.print_exc()
