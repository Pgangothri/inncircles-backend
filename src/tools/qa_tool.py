import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_core.prompts import PromptTemplate


def answer_questions_with_llm(
    questions: List[str],
    retriever,
    model_name: str = "gpt-4o",
    temperature: float = 0.1
) -> List[Dict]:
    """
    Improved RetrievalQA answering tool.
    Uses RetrievalQAWithSourcesChain for better grounded answers.

    Returns:
        List of {"question": ..., "answer": ...}
    """
    print(f"[💬] Initializing LLM: {model_name}")
    llm = ChatOpenAI(model=model_name, temperature=temperature)

    QA_PROMPT = PromptTemplate(
        
       input_variables=["context", "question"],
       template="""
You are a highly capable compliance assistant helping complete a contractor pre-qualification form.

Analyze the CONTEXT carefully and provide the most accurate answer possible based on the information given . 
If the answer is not explicitly stated but can be inferred logically, provide the inferred answer and mention it is an inference.  
If there is absolutely no relevant information, respond with:
"I cannot determine the answer from the provided documents."

---

📄 CONTEXT:
{context}

❓ QUESTION:
{question}

---

✅ ANSWER (clear and concise):
"""
)


    qa_chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="map_reduce",
        chain_type_kwargs={"question_prompt": QA_PROMPT},
        return_source_documents=True
    )

    results = []
    print(f"[🔍] Answering {len(questions)} questions...")

    for i, q in enumerate(questions, 1):
        try:
            print(f"  Q{i}: {q}")
            response = qa_chain.invoke({"question": q})
            answer = response.get("answer", "").strip()
            sources = response.get("sources", "")

            if not answer:
                answer = "I cannot find the answer in the provided documents."

            print(f"    ✅ Answer: {answer}")
            if sources:
                print(f"    📂 Sources: {sources}")

            results.append({
                "question": q,
                "answer": f"{answer} (Sources: {sources})" if sources else answer
            })

        except Exception as e:
            results.append({"question": q, "answer": f"[Error]: {str(e)}"})

    return results
