import os
from typing import List
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# === Enhanced FAISS Builder ===
def build_faiss_index_from_docs(
    docs: List[dict],
    persist_path: str = "faiss_index",
    chunk_size: int = 700,
    chunk_overlap: int = 150,
    min_chunk_length: int = 50
) -> FAISS:
    """
    Converts documents into a FAISS vector index with optimized chunking.

    Args:
        docs: [{"text": str, "source": str}]
        persist_path: Directory to save FAISS index
        chunk_size: Max length of chunks
        chunk_overlap: Overlap to maintain context
        min_chunk_length: Filter out tiny useless chunks

    Returns:
        FAISS vector store
    """
    if not docs:
        raise ValueError("No documents provided to index.")

    print(f"[🔍] Indexing {len(docs)} documents...")

    # Step 1: Convert to LangChain Document objects
    langchain_docs = [
        Document(page_content=d["text"].strip(), metadata={"source": d.get("source", "unknown")})
        for d in docs if isinstance(d.get("text"), str) and d["text"].strip()
    ]

    # Step 2: Chunking with filters
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " "]
    )
    raw_chunks = splitter.split_documents(langchain_docs)
    chunks = [c for c in raw_chunks if len(c.page_content.strip()) >= min_chunk_length]

    print(f"[📚] Split into {len(chunks)} chunks (filtered from {len(raw_chunks)} raw chunks)")

    # Step 3: Embedding and storing
    embedding_model = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embedding_model)

    # Step 4: Save index
    if persist_path:
        os.makedirs(persist_path, exist_ok=True)
        vectorstore.save_local(persist_path)
        print(f"[💾] FAISS index saved to '{persist_path}/'")

    return vectorstore


# === FAISS Loader ===
def load_faiss_index(persist_path: str = "faiss_index") -> FAISS:
    """
    Loads an existing FAISS vector store.
    """
    if not os.path.exists(persist_path):
        raise FileNotFoundError(f"FAISS index path '{persist_path}' not found.")

    embedding_model = OpenAIEmbeddings()
    vectorstore = FAISS.load_local(
        persist_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )
    print(f"[📦] Loaded FAISS index from '{persist_path}/'")
    return vectorstore
