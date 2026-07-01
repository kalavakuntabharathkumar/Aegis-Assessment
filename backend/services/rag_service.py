import os
import requests
from typing import List
from pinecone._client import Pinecone


def get_embedding_openrouter(text: str) -> List[float]:
    """Primary embedding via OpenRouter (OpenAI text-embedding-3-small)."""
    response = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        json={"model": "openai/text-embedding-3-small", "input": text},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["embedding"]


def get_embedding_huggingface(text: str) -> List[float]:
    """
    Fallback embedding via Hugging Face Inference API.
    Uses sentence-transformers/all-MiniLM-L6-v2 (384-dim, free tier).
    """
    hf_token = os.getenv("HUGGINGFACE_API_KEY", "")
    headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
    response = requests.post(
        "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2",
        headers=headers,
        json={"inputs": text[:512], "options": {"wait_for_model": True}},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if isinstance(result[0], list):
        embedding = result[0]
    else:
        embedding = result
    return embedding


def get_embedding(text: str) -> List[float]:
    """
    Get text embedding with automatic fallback:
      1. OpenRouter (OpenAI text-embedding-3-small) — primary
      2. Hugging Face Inference API (all-MiniLM-L6-v2) — fallback
    """
    try:
        return get_embedding_openrouter(text)
    except Exception as primary_err:
        print(f"OpenRouter embedding failed ({primary_err}), falling back to HuggingFace")
        return get_embedding_huggingface(text)


def query_pinecone(embedding: List[float], top_k: int = 5) -> List[dict]:
    """Returns a list of dicts: {text, source, chunk_index}."""
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(host=os.getenv("PINECONE_HOST"))
    results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
    chunks = []
    for match in results.get("matches", []):
        metadata = match.get("metadata", {})
        text = metadata.get("text", metadata.get("content", str(metadata)))
        if text:
            chunks.append({
                "text": text,
                "source": metadata.get("source", metadata.get("filename", "unknown")),
                "chunk_index": int(metadata.get("chunk_index", metadata.get("chunk_id", 0))),
            })
    return chunks


def retrieve_relevant_chunks(skills: List[str], resume_text: str) -> List[dict]:
    """
    Returns a list of chunk dicts: {"text": ..., "source": ..., "chunk_index": ...}.
    Falls back to an empty list on any error.
    """
    query_text = f"Technical interview questions about: {', '.join(skills[:8])}. Context: {resume_text[:500]}"
    try:
        embedding = get_embedding(query_text)
        return query_pinecone(embedding)
    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return []
