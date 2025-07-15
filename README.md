**# Manus AI - General Agent Assignment

This project implements a LangGraph-based general-purpose agent that processes contractor Pre-Qualification Questionnaires (PQQs). It extracts questions from form files using OCR and LLM, then answers them by retrieving relevant information from supporting documents using FAISS vector search and OpenAI GPT-4o.

## How to Run

1. **Clone the repository**:
   ```bash
   git clone git@github.com:Pgangothri/inncircles-backend.git

2. **Go to Project**
    ```bash
     cd your project
3. **Create Virtual Environment**
   ```bash
   python -m venv venv
4. **Activate the Environment**
   ```bash
   venv/Scripts/activate  #on windows
   source ./venv/bin/activate #on Linux
5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
6.  **Configure environment variables**
    - Create a .env file with your keys
    <pre><code>OPENAI_API_KEY=your_openai_key 
    SERPAPI_KEY=your_serpapi_key 
    DAYTONA_API_KEY=your_daytona_key 
    DAYTONA_API_URL=https://app.daytona.io/api </code></pre>
7.  **Prepare Workspace**
   - Organize your files as follows:
      **📂 Workspace Structure**
     workspace/
     
     ├── Form/ # Place Pre-Qual Form (PDF/DOCX)
     
     ├── Knowledge Base/ # Place supporting documents here
     
     ├── images/ # Used by VisionAgent for screenshots/OCR
     
     └── memory.json # Created automatically to store agent memory
8. **Run the Agent**
   ```bash
   python src/agent/core_agent.py
9. **Edit the default prompt in core_agent.py if needed:**

   prompt = "Consider the pre-qual questionnaire as form containing multiple questions and answer all of them from the rest of the files."





     




