import os
import sys
import re
from typing import TypedDict, List, Dict, Optional
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from pydantic import BaseModel

# Load env vars & set project root
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# === Imports ===
from src.tools.files_tool import FilesTool
from src.agent.planning_agent import planning_agent
from src.agent.plan_schema import Plan, Subtask, AgentEnum
from src.utils.xml_formatter import xml_wrap
from src.utils.config_loader import load_config
from src.utils.logging_config import logger
from src.tools.question import extract_questions_from_form
from src.tools.vector_store_tool import build_faiss_index_from_docs, load_faiss_index
from src.tools.qa_tool import answer_questions_with_llm
from src.agent.reasoning_engine import reasoning_for_step
from src.memory.memory_manager import MemoryManager

# === Load Config ===
agent_cfg = load_config("agent_config.yaml")["agent"]
MAX_STEPS = agent_cfg.get("max_steps", 5)
OUTPUT_FORMAT = agent_cfg.get("output_format", "xml")

# === Agent State ===
class AgentState(TypedDict):
    task_id: str
    messages: List
    status: str
    plan: Dict
    results: List[str]
    errors: List[str]
    docs: List
    questions: List[str]
    answers: List[Dict]
    step_index: int
    image_base64: Optional[str]

# === Tool Runners ===
def run_document_agent(knowledge_base_path: str):
    try:
        logger.info("[DocumentAgent] Loading documents...")
        files_tool = FilesTool()
        documents = files_tool.extract_knowledge_documents(knowledge_base_path)
        if not documents:
            raise ValueError("No documents found in the Knowledge Base folder")
        logger.info(f"[DocumentAgent] Loaded {len(documents)} documents")
        return documents
    except Exception as e:
        logger.exception("[DocumentAgent] Failed to load documents")
        raise

def run_question_agent(form_path: str):
    try:
        logger.info("[QuestionAgent] Extracting questions from form...")
        questions = extract_questions_from_form(form_path)
        if not questions:
            raise ValueError("No questions extracted from form")
        logger.info(f"[QuestionAgent] Extracted {len(questions)} questions")
        return questions
    except Exception as e:
        logger.exception("[QuestionAgent] Failed to extract questions")
        raise

def run_retrieval_agent(questions, docs):
    try:
        logger.info("[RetrievalAgent] Building FAISS index and answering questions...")
        build_faiss_index_from_docs(docs)
        retriever = load_faiss_index().as_retriever()
        answers = answer_questions_with_llm(questions, retriever)
        logger.info(f"[RetrievalAgent] Answered {len(answers)} questions")
        return answers
    except Exception as e:
        logger.exception("[RetrievalAgent] Failed to retrieve answers")
        raise

# === Orchestrator ===
def orchestrate_step(state: AgentState) -> AgentState:
    try:
        plan = Plan(**state["plan"])
        current_step = plan.subtasks[state["step_index"]]
        agent = current_step.assigned_agent
        logger.info(f"[Orchestrator] Executing step {state['step_index'] + 1}/{len(plan.subtasks)}: {agent}")

        if agent == AgentEnum.DocumentAgent:
            state["docs"] = run_document_agent("workspace/Knowledge Base")
            state["results"].append(f"[DocumentAgent] Loaded {len(state['docs'])} documents")

        elif agent == AgentEnum.QuestionAgent:
            state["questions"] = run_question_agent("workspace/Form")
            state["results"].append(f"[QuestionAgent] Extracted {len(state['questions'])} questions")

        elif agent == AgentEnum.RetrievalAgent:
            if not state.get("docs") or not state.get("questions"):
                raise ValueError("Missing documents or questions for RetrievalAgent")
            state["answers"] = run_retrieval_agent(state["questions"], state["docs"])
            # Append answers to results for final XML output
            for a in state["answers"]:
                state["results"].append(f"Q: {a['question']}\nA: {a['answer']}")

        elif agent == AgentEnum.ReadAgent:
            tool = FilesTool()
            extracted = tool.extract_from_all()
            state["results"].append(f"[ReadAgent] Extracted data: {extracted}")

        elif agent == AgentEnum.ShellAgent:
            from src.tools.shell_tool import ShellTool
            output = ShellTool().execute("echo Hello from ShellAgent")
            state["results"].append(output)

        elif agent == AgentEnum.VisionAgent:
            from src.tools.vision_tool import VisionTool
            if not state.get("image_base64"):
                raise ValueError("No screenshot image found for VisionAgent")
            result = VisionTool().analyze_base64_image(state["image_base64"])
            state["results"].append(result)

        elif agent == AgentEnum.CodeAgent:
            from src.tools.code_interpreter import CodeInterpreterTool
            result = CodeInterpreterTool().run("print(2 + 2)")
            state["results"].append(result)

        elif agent == AgentEnum.ComputerAgent:
            from src.tools.computer_use import ComputerUseTool
            xml_output = ComputerUseTool().take_screenshot()
            match = re.search(r"<data>(.*?)</data>", xml_output, re.DOTALL)
            if not match:
                raise ValueError("Failed to extract image base64 from screenshot XML")
            base64_img = match.group(1).strip()
            state["image_base64"] = base64_img
            state["results"].append("Screenshot taken successfully.")

        else:
            raise ValueError(f"Unsupported agent type: {agent}")

        state["step_index"] += 1
        state["status"] = "executing"

    except Exception as e:
        logger.exception("[Orchestrator] Step failed")
        state["errors"].append(str(e))
        state["status"] = "failed"

    return state

# === Planner ===
def planner(state: AgentState) -> AgentState:
    try:
        prompt = state["messages"][-1].content.strip()
        if not prompt:
            raise ValueError("Empty prompt provided.")
        logger.info("[Planner] Planning task subtasks...")
        plan = planning_agent(prompt)
        state["plan"] = plan.model_dump()
        state["status"] = "executing"
    except Exception as e:
        logger.exception("[Planner] Planning failed")
        state["status"] = "failed"
        state["plan"] = {"goal": "Planning failed due to error.", "subtasks": []}
        state["errors"].append(f"Planning error: {str(e)}")
    return state

# === Finalizer ===
def finalize(state: AgentState) -> AgentState:
    logger.info("[Finalizer] Finalizing agent output...")

    qa_text = "\n".join(state["results"]) if state["results"] else "<no result>"

    tools_used = []
    reasoning = {"thought": "No steps executed.", "next_action": "Abort"}
    try:
        plan_obj = Plan(**state["plan"])
        tools_used = [step.assigned_agent.value for step in plan_obj.subtasks]
        if state["step_index"] > 0 and plan_obj.subtasks:
            last_agent = plan_obj.subtasks[state["step_index"] - 1].assigned_agent
            reasoning = reasoning_for_step(
                agent=last_agent,
                step_index=state["step_index"] - 1,
                total_steps=len(tools_used)
            )
    except Exception as e:
        logger.exception("[Finalizer] Plan parsing failed")
        state["errors"].append(f"Finalization error: {str(e)}")

    xml_output = xml_wrap(
        task_id=state["task_id"],
        status="completed" if not state["errors"] else "failed",
        current_step="finalize",
        tools_used=tools_used,
        reasoning=reasoning,
        result={
            "success": not bool(state["errors"]),
            "data": qa_text,
            "errors": state["errors"]
        }
    )

    state["results"].append(xml_output)
    state["status"] = "completed"

    MemoryManager().save_interaction(
        task_id=state["task_id"],
        user_prompt=state["messages"][-1].content,
        plan=state["plan"],
        answers=state["answers"],
        errors=state["errors"]
    )
    return state

# === Controller ===
def should_continue(state: AgentState) -> str:
    if state["status"] in ["failed", "completed"]:
        return "finalize"
    plan = Plan(**state["plan"])
    if state["step_index"] >= len(plan.subtasks):
        return "finalize"
    return "orchestrate_step"

# === LangGraph Setup ===
builder = StateGraph(AgentState)
builder.add_node("planner", planner)
builder.add_node("orchestrate_step", orchestrate_step)
builder.add_node("finalize", finalize)
builder.set_entry_point("planner")
builder.add_conditional_edges("planner", should_continue, {
    "orchestrate_step": "orchestrate_step",
    "finalize": "finalize"
})
builder.add_conditional_edges("orchestrate_step", should_continue, {
    "orchestrate_step": "orchestrate_step",
    "finalize": "finalize"
})
builder.add_edge("finalize", END)
agent_graph = builder.compile()

# === Agent Runner ===
def run_agent(task_id: str, user_prompt: str) -> str:
    state = AgentState(
        task_id=task_id,
        messages=[HumanMessage(content=user_prompt)],
        status="planning",
        plan={},
        results=[],
        errors=[],
        docs=[],
        questions=[],
        answers=[],
        step_index=0,
        image_base64=None
    )
    final_state = agent_graph.invoke(state)
    return final_state["results"][-1] if final_state["results"] else "<error>No result returned</error>"

# === CLI Test ===
if __name__ == "__main__":
    prompt = "Consider the pre-qual questionnaire as form containing multiple questions and answer all of them from the rest of the files."
    print(run_agent("agent_task_003", prompt))
