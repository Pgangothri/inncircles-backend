import os
import sys
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# ✅ Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.tools.files_tool import FilesTool

# Load environment variables
load_dotenv()

def extract_questions_from_form(form_path: str) -> List[str]:
    """
    Extracts structured questions from a contractor pre-qualification form using OCR and GPT-4o.
    Returns a list of plain text question strings.
    """
    tool = FilesTool(form_path)

    # 🔍 Extract OCR text from form
    print("📄 OCR: Extracting text from form...")
    extracted = tool.extract_from_all()

    form_text = ""
    for doc in extracted:
        if "pre qual" in doc["file"].lower():
            form_text = doc["content"]
            break

    if not form_text:
        raise ValueError("❌ ERROR: Could not find form text.")

    print(f"[✅] OCR text length: {len(form_text)} characters")

    # 🤖 Use GPT-4o to extract questions
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = f"""
You are an expert in analyzing contractor pre-qualification forms. The text below is extracted from an EHS Contractor Pre-Qualification Form using OCR.

Your task is to extract **all questions, fields, and instructions** that a contractor is expected to fill out.

Organize the output as a **numbered plain-text list**, grouped by section.

Include:
- All direct questions
- All yes/no checkboxes with explanations (e.g., "Does your company have a written safety program? (Yes/No)")
- All conditional requirements (e.g., "If yes, attach certificate")
- All statistical data requests with formula instructions
- All document submission requirements
- Any certification, compliance, signature, or declaration fields

---

📄 FORM TEXT (OCR EXTRACTED):

{form_text}

---

📌 Output Format:

Use this format:

1. [Section Name]
2. What is your company name?
3. What is your company address?
4. What is your automobile insurance company name and telephone number? (Attach certificate showing Innophos as additional insured)
5. Does your company have a written safety program? (Yes/No) (If yes, submit Table of Contents with your completed questionnaire)
6. Does your company have a written procedure to ensure safety and health issues are preplanned into each job? (Yes/No)
...
[n]. What is the name and signature of the person completing this questionnaire?

🧠 Format Guidelines:
- Keep numbering continuous across sections
- Do **not** return in JSON format — just numbered list
- Be exhaustive and do **not skip** any form field, checkbox, or instruction
"""


    print("🧠 Extracting structured questions using GPT-4o...")
    response = llm.invoke(prompt)

    # Split into list of questions
    questions = [line.strip() for line in response.content.strip().split("\n") if line.strip()]
    print(f"✅ Extracted {len(questions)} questions")
    return questions

