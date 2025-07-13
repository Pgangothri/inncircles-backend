import json
import os
from typing import Dict, List
from datetime import datetime

from src.utils.logging_config import logger  # ✅ import logger


class MemoryManager:
    def __init__(self, file_path: str = "workspace/memory.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            with open(self.file_path, "w") as f:
                json.dump({"interactions": []}, f)
            logger.info(f"[MemoryManager] Created new memory file at {self.file_path}")
        else:
            logger.info(f"[MemoryManager] Using existing memory file at {self.file_path}")

    def save_interaction(self, task_id: str, user_prompt: str, plan: Dict, answers: List[Dict], errors: List[str]):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)

            interaction = {
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id,
                "prompt": user_prompt,
                "plan": plan,
                "answers": answers,
                "errors": errors
            }

            data["interactions"].append(interaction)

            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"[MemoryManager] Saved interaction for task_id={task_id}")

        except Exception as e:
            logger.exception(f"[MemoryManager] Failed to save interaction: {e}")

    def load_memory(self) -> List[Dict]:
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            logger.info("[MemoryManager] Loaded memory history")
            return data.get("interactions", [])
        except Exception as e:
            logger.exception(f"[MemoryManager] Failed to load memory: {e}")
            return []

    def retrieve_relevant_memories(self, query: str, top_k: int = 3) -> List[Dict]:
        try:
            logger.info(f"[MemoryManager] Retrieving relevant memories for query: {query}")
            all_memories = self.load_memory()
            query_terms = set(query.lower().split())

            def score(mem):
                prompt_terms = set(mem["prompt"].lower().split())
                return len(query_terms & prompt_terms)

            sorted_memories = sorted(all_memories, key=score, reverse=True)
            top_memories = sorted_memories[:top_k]
            logger.info(f"[MemoryManager] Retrieved {len(top_memories)} relevant memories")
            return top_memories

        except Exception as e:
            logger.exception(f"[MemoryManager] Failed to retrieve relevant memories: {e}")
            return []
