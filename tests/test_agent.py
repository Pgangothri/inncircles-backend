import unittest
import os
import sys

# Add src/ to sys.path so we can import from agent/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agent.core_agent import run_agent


class TestAgentDocumentWorkflow(unittest.TestCase):

    def setUp(self):
        self.prompt_valid = (
            "Consider the pre-qual questionnaire as form containing multiple questions "
            "and answer all of them from the rest of the files."
        )
        self.prompt_empty = ""

    def test_agent_generates_valid_response(self):
        task_id = "test_task_valid"
        result = run_agent(task_id, self.prompt_valid)

        self.assertIsInstance(result, str)
        self.assertIn("<agent_response>", result)
        self.assertIn("<task_id>", result)
        self.assertIn("<status>", result)
        self.assertIn("<tools_used>", result)
        self.assertIn("<reasoning>", result)
        self.assertIn("<result>", result)
        self.assertIn("<data>", result)

        if "<status>failed</status>" in result:
            print("⚠️ Agent encountered failure: Check logs for root cause.")
        else:
            print("✅ Agent completed task successfully.")

    def test_agent_handles_empty_prompt(self):
        task_id = "test_task_empty"
        result = run_agent(task_id, self.prompt_empty)

        self.assertIsInstance(result, str)
        self.assertIn("<agent_response>", result)
        self.assertIn("<status>failed</status>", result)
        print("✅ Agent gracefully handled empty prompt.")


if __name__ == "__main__":
    unittest.main()
