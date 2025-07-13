import os
import sys

# Add the `src` directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# ✅ Now import
from agent.core_agent import run_agent

prompt = "Consider the pre-qual questionnaire as form containing multiple questions and answer all of them from the rest of the files."
result = run_agent("agent_task_003", prompt)
print(result)
