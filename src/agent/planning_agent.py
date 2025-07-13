import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.plan_schema import Plan, AgentEnum
from src.utils.logging_config import logger
from src.memory.memory_manager import MemoryManager

load_dotenv()

# === System Prompt Template ===
PLANNER_SYSTEM_PROMPT = """
You are a planning agent responsible for decomposing user tasks into subtasks.
Each subtask must be assigned to ONE of the following specialized agents:

- DocumentAgent:  Read and extract information from Knowledge Base documents. 
- ReadAgent: Just getting an text from documents.
- QuestionAgent: Extract questions using OCR/LLM from PDFs or DOCX files.
- RetrievalAgent: Answer questions using document context (RAG).
- ShellAgent: Execute shell commands (e.g., terminal).
- VisionAgent: Analyze screenshots/images using OCR.
- CodeAgent: Run code snippets in Python.
- ComputerAgent: Interact with the desktop (e.g., take screenshots).

RULES:
- Use ONLY the exact agent names listed above (case-sensitive).
- DO NOT invent new agents.
- Return your response in the following JSON format:

{
  "objective": "...",
  "subtasks": [
    { "description": "...", "assigned_agent": "..." },
    ...
  ]
}
"""

llm = ChatOpenAI(model="gpt-4o", temperature=0)


def extract_json_from_markdown(text: str) -> str:
    """Extract JSON from markdown-style output."""
    if "```" in text:
        return text.split("```")[1].replace("json", "", 1).strip()
    return text.strip()


def reorder_subtasks(subtasks: list[dict]) -> list[dict]:
    """Ensure correct agent execution order."""
    priority = {
        "computer_agent": 0,
        "document_agent": 1,
        "read_agent": 2,
        "question_agent": 3,
        "retrieval_agent": 4,
        "vision_agent": 5,
        "shell_agent": 6,
        "code_agent": 7,
    }
    return sorted(subtasks, key=lambda s: priority.get(s["assigned_agent"], 99))


def normalize_agent_name(name: str) -> str:
    """Convert CamelCase (e.g., ComputerAgent) to snake_case (computer_agent)."""
    if name.endswith("Agent"):
        return name[:-5].lower() + "_agent"
    return name.lower()


def planning_agent(user_prompt: str) -> Plan:
    logger.info("[PlanningAgent] Generating plan from prompt...")

    memory = MemoryManager()
    relevant_memories = memory.retrieve_relevant_memories(user_prompt)

    memory_context = "".join(
        f"\n---\nPrevious Task: {m['prompt']}\nPlan: {m['plan']}\nAnswers: {m['answers']}\n"
        for m in relevant_memories
    )

    full_system_prompt = PLANNER_SYSTEM_PROMPT + "\n\n[Context from memory:]" + memory_context

    messages = [
        SystemMessage(content=full_system_prompt),
        HumanMessage(content=user_prompt)
    ]

    try:
        response = llm.invoke(messages)
        plan_json_str = extract_json_from_markdown(response.content)
        logger.info("[PlanningAgent] Raw LLM response:\n" + plan_json_str)

        raw_plan = json.loads(plan_json_str)

        if "objective" not in raw_plan or "subtasks" not in raw_plan:
            raise ValueError("Missing 'objective' or 'subtasks' in plan")

        # Rename 'objective' → 'goal'
        raw_plan["goal"] = raw_plan.pop("objective")

        # Normalize subtasks
        normalized_subtasks = []
        for i, step in enumerate(raw_plan["subtasks"]):
            agent_snake_case = normalize_agent_name(step["assigned_agent"])
            if agent_snake_case not in AgentEnum._value2member_map_:
                raise ValueError(f"Invalid agent: {step['assigned_agent']}")
            normalized_subtasks.append({
                "step": i,
                "description": step["description"],
                "assigned_agent": agent_snake_case
            })

        raw_plan["subtasks"] = reorder_subtasks(normalized_subtasks)

        plan = Plan(**raw_plan)
        logger.info("[PlanningAgent] Final Plan:\n" + json.dumps(plan.model_dump(), indent=2))
        return plan

    except Exception as e:
        logger.exception("[PlanningAgent] Planning failed")
        raise RuntimeError(f"Planning failed: {e}")
