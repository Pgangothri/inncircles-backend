import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate


def answer_questions_with_llm(
    questions: List[str],
    retriever,
    model_name: str = "gpt-4o",
    temperature: float = 0.1
) -> List[Dict]:
    """
    Answers questions using Retrieval-Augmented QA with GPT-4o and a custom retriever.

    Args:
        questions: list of question strings
        retriever: LangChain retriever object (e.g., FAISS retriever)
        model_name: OpenAI model to use
        temperature: completion randomness

    Returns:
        List of {"question": ..., "answer": ...}
    """
    print(f"[💬] Initializing LLM: {model_name}")
    llm = ChatOpenAI(model=model_name, temperature=temperature)

    QA_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a highly capable compliance assistant helping complete a contractor pre-qualification form.

Your task is to answer the QUESTION below using only the relevant CONTEXT extracted from company documentation.
Analyze all the provided context and use it to accurately answer the question.

Respond clearly and concisely.

---

📄 CONTEXT:
{context}

❓ QUESTION:
{question}

---

✅ ANSWER:
"""
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="map_reduce",
        chain_type_kwargs={"question_prompt": QA_PROMPT}
        # Optional: return_source_documents=True
    )

    results = []
    print(f"[🔍] Answering {len(questions)} questions...")
    for i, q in enumerate(questions, 1):
        try:
            print(f"  Q{i}: {q}")
            answer = qa_chain.run(q)
            results.append({"question": q, "answer": answer})
        except Exception as e:
            results.append({"question": q, "answer": f"[Error]: {str(e)}"})

    return results
