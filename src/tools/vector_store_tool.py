# tools/vector_store_tool.py

import os
from typing import List
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def build_faiss_index_from_docs(
    docs: List[dict],
    persist_path: str = "faiss_index",
    chunk_size: int = 800,
    chunk_overlap: int = 100
) -> FAISS:
    """
    Converts a list of dicts (with 'text' and 'source') into a FAISS vector index.

    Args:
        docs: List of {"text": str, "source": str}
        persist_path: Directory to save FAISS index
        chunk_size: Character length of each chunk
        chunk_overlap: Overlap between chunks

    Returns:
        FAISS vector store
    """
    if not docs:
        raise ValueError("No documents provided to index.")

    print(f"[🔍] Indexing {len(docs)} documents...")

    # Step 1: Convert to LangChain Document objects
    langchain_docs = [
        Document(page_content=d["text"], metadata={"source": d["source"]})
        for d in docs if isinstance(d["text"], str)
    ]

    # Step 2: Chunk large docs
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(langchain_docs)
    print(f"[📚] Split into {len(chunks)} chunks")

    # Step 3: Embed and store
    embedding_model = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embedding_model)

    # Step 4: Persist index
    if persist_path:
        os.makedirs(persist_path, exist_ok=True)
        vectorstore.save_local(persist_path)
        print(f"[💾] FAISS index saved to '{persist_path}/'")

    return vectorstore


def load_faiss_index(persist_path: str = "faiss_index") -> FAISS:
    """
    Loads a FAISS vector store from disk.
    """
    if not os.path.exists(persist_path):
        raise FileNotFoundError(f"FAISS index path '{persist_path}' not found.")

    embedding_model = OpenAIEmbeddings()
    vectorstore = FAISS.load_local(
        persist_path,
        embedding_model,
        allow_dangerous_deserialization=True  # ✅ Acceptable for local use
    )
    print(f"[📦] Loaded FAISS index from '{persist_path}/'")
    return vectorstore
