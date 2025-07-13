# src/agent/reasoning_engine.py

from src.agent.plan_schema import AgentEnum
from src.utils.logging_config import logger

def reasoning_for_step(agent: AgentEnum, step_index: int, total_steps: int) -> dict:
    """Return the reasoning/thought and next_action for the current step."""
    thoughts = {
        AgentEnum.DocumentAgent: "Load and analyze company documents to extract relevant content.",
        AgentEnum.ReadAgent: "Read file contents to understand their structure or metadata.",
        AgentEnum.QuestionAgent: "Extract questions from the pre-qualification form using OCR or LLM.",
        AgentEnum.RetrievalAgent: "Retrieve answers from document context using vector similarity.",
        AgentEnum.ComputerAgent: "Capture a screenshot of the system for further analysis.",
        AgentEnum.VisionAgent: "Analyze the screenshot using OCR to extract on-screen information.",
        AgentEnum.CodeAgent: "Execute a Python code snippet for computation or testing.",
        AgentEnum.ShellAgent: "Run a shell command and return the output."
    }

    next_action = (
        f"Execute step {step_index + 2} of {total_steps}" 
        if step_index + 1 < total_steps 
        else "Finalize the task"
    )

    return {
        "thought": thoughts.get(agent, "Perform assigned task using the appropriate agent."),
        "next_action": next_action
    }
