"""
backend/ingest.py
-----------------
Standalone one-time script that builds the Pinecone knowledge base from ML
textbook PDFs stored in ./books/.

Usage:
    python backend/ingest.py            # full run: embed + upsert
    python backend/ingest.py --dry-run  # chunk only, no API calls

Requires env vars: PINECONE_API_KEY, PINECONE_HOST, OPENROUTER_API_KEY
"""

import argparse
import os
import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Tuple

import fitz  # PyMuPDF


BOOKS_DIR = Path(__file__).parent.parent / "books"
CHUNK_TOKENS = 500
OVERLAP_TOKENS = 50
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 5

BOOK_TITLES: Dict[str, str] = {
    "mitchell_ml": "Machine Learning (Mitchell)",
    "bishop_prml": "Pattern Recognition and Machine Learning (Bishop)",
    "burkov_100page": "The Hundred-Page Machine Learning Book (Burkov)",
}


def derive_book_title(filename: str) -> str:
    stem = Path(filename).stem.lower()
    for key, title in BOOK_TITLES.items():
        if key in stem:
            return title
    return stem.replace("_", " ").title()


def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)


def approx_token_count(text: str) -> int:
    return max(1, len(text) // 4)


def split_into_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r"\n{2,}", text)
    cleaned = []
    for p in paragraphs:
        p = p.strip()
        if p:
            cleaned.append(p)
    return cleaned


def chunk_text(text: str, chunk_tokens: int = CHUNK_TOKENS, overlap_tokens: int = OVERLAP_TOKENS) -> List[str]:
    paragraphs = split_into_paragraphs(text)

    chunks: List[str] = []
    current_parts: List[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = approx_token_count(para)

        if para_tokens > chunk_tokens:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_tokens = 0

            words = para.split()
            words_per_chunk = chunk_tokens * 4
            words_per_overlap = overlap_tokens * 4
            start = 0
            while start < len(words):
                end = min(start + words_per_chunk, len(words))
                chunk_text_part = " ".join(words[start:end])
                chunks.append(chunk_text_part)
                if end == len(words):
                    break
                start = end - words_per_overlap
            continue

        if current_tokens + para_tokens > chunk_tokens and current_parts:
            chunks.append("\n\n".join(current_parts))

            overlap_parts: List[str] = []
            overlap_count = 0
            for part in reversed(current_parts):
                part_tokens = approx_token_count(part)
                if overlap_count + part_tokens > overlap_tokens:
                    break
                overlap_parts.insert(0, part)
                overlap_count += part_tokens
            current_parts = overlap_parts
            current_tokens = overlap_count

        current_parts.append(para)
        current_tokens += para_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return [c for c in chunks if c.strip()]


def get_embedding_openrouter(text: str) -> List[float]:
    import requests
    response = requests.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        json={"model": "openai/text-embedding-3-small", "input": text},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def get_embedding_huggingface(text: str) -> List[float]:
    import requests
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
        return result[0]
    return result


def get_embedding(text: str) -> List[float]:
    try:
        return get_embedding_openrouter(text)
    except Exception as primary_err:
        print(f"  [warn] OpenRouter embedding failed ({primary_err}), falling back to HuggingFace")
        return get_embedding_huggingface(text)


def upsert_batch_with_retry(index, vectors: List[dict], attempt: int = 1) -> bool:
    try:
        index.upsert(vectors=vectors)
        return True
    except Exception as e:
        if attempt >= MAX_RETRIES:
            print(f"  [error] Upsert failed after {MAX_RETRIES} attempts: {e}")
            return False
        wait = RETRY_DELAY * attempt
        print(f"  [retry] Upsert attempt {attempt} failed ({e}), retrying in {wait}s...")
        time.sleep(wait)
        return upsert_batch_with_retry(index, vectors, attempt + 1)


def process_pdf(pdf_path: Path) -> List[Tuple[int, str]]:
    print(f"\nReading: {pdf_path.name}")
    text = extract_text_from_pdf(pdf_path)
    print(f"  Extracted {len(text):,} characters")
    chunks = chunk_text(text)
    print(f"  Split into {len(chunks)} chunks (~{CHUNK_TOKENS} tokens each, {OVERLAP_TOKENS} overlap)")
    return list(enumerate(chunks))


def dry_run(pdf_paths: List[Path]) -> None:
    print("=" * 60)
    print("DRY RUN — no embeddings or Pinecone calls will be made")
    print("=" * 60)

    total_chunks = 0
    for pdf_path in pdf_paths:
        indexed_chunks = process_pdf(pdf_path)
        total_chunks += len(indexed_chunks)

        if indexed_chunks:
            sample_idx, sample_text = indexed_chunks[0]
            preview = sample_text[:300].replace("\n", " ")
            print(f"\n  Sample chunk #0 ({approx_token_count(sample_text)} est. tokens):")
            print(f"  >>> {preview}{'...' if len(sample_text) > 300 else ''}")

            if len(indexed_chunks) > 1:
                mid_idx = len(indexed_chunks) // 2
                mid_text = indexed_chunks[mid_idx][1]
                mid_preview = mid_text[:200].replace("\n", " ")
                print(f"\n  Sample chunk #{mid_idx} ({approx_token_count(mid_text)} est. tokens):")
                print(f"  >>> {mid_preview}{'...' if len(mid_text) > 200 else ''}")

    print("\n" + "=" * 60)
    print(f"Total chunks across all books: {total_chunks}")
    print(f"Estimated embedding calls needed: {total_chunks}")
    print(f"Estimated Pinecone upsert batches: {(total_chunks + BATCH_SIZE - 1) // BATCH_SIZE}")
    print("=" * 60)
    print("Run without --dry-run to embed and upsert.")


def full_run(pdf_paths: List[Path]) -> None:
    from pinecone._client import Pinecone

    pinecone_key = os.getenv("PINECONE_API_KEY")
    pinecone_host = os.getenv("PINECONE_HOST")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    missing = []
    if not pinecone_key:
        missing.append("PINECONE_API_KEY")
    if not pinecone_host:
        missing.append("PINECONE_HOST")
    if not openrouter_key:
        missing.append("OPENROUTER_API_KEY")
    if missing:
        print(f"[error] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index(host=pinecone_host)
    print(f"Connected to Pinecone index at {pinecone_host}")

    grand_total = 0
    grand_upserted = 0

    for pdf_path in pdf_paths:
        indexed_chunks = process_pdf(pdf_path)
        filename = pdf_path.name
        book_title = derive_book_title(filename)
        total = len(indexed_chunks)

        batch: List[dict] = []
        upserted = 0

        for chunk_index, chunk_text_val in indexed_chunks:
            vector_id = f"{pdf_path.stem}__chunk_{chunk_index}"

            embedding = get_embedding(chunk_text_val)

            batch.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "text": chunk_text_val[:8000],
                    "source": filename,
                    "chunk_index": chunk_index,
                    "book_title": book_title,
                },
            })

            if len(batch) >= BATCH_SIZE:
                success = upsert_batch_with_retry(index, batch)
                if success:
                    upserted += len(batch)
                grand_total += len(batch)
                batch = []
                print(f"  Processed {grand_total + len(batch)}/{total} chunks from {filename}")

        if batch:
            success = upsert_batch_with_retry(index, batch)
            if success:
                upserted += len(batch)
            grand_total += len(batch)
            print(f"  Processed {grand_total}/{total} chunks from {filename}")

        grand_upserted += upserted
        print(f"  Done: {upserted}/{total} chunks upserted for {filename}")

    print("\n" + "=" * 60)
    print(f"Ingestion complete.")
    print(f"Total chunks processed: {grand_total}")
    print(f"Total vectors upserted: {grand_upserted}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest ML textbook PDFs into the Pinecone knowledge base."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chunk PDFs and show stats without calling embeddings or Pinecone.",
    )
    parser.add_argument(
        "--books-dir",
        type=str,
        default=str(BOOKS_DIR),
        help=f"Path to folder containing PDF files (default: {BOOKS_DIR})",
    )
    args = parser.parse_args()

    books_dir = Path(args.books_dir)
    if not books_dir.exists():
        print(f"[info] Books directory not found, creating: {books_dir}")
        books_dir.mkdir(parents=True, exist_ok=True)

    pdf_paths = sorted(books_dir.glob("*.pdf"))

    if not pdf_paths:
        print(f"[warn] No PDF files found in {books_dir}")
        print(f"       Place your ML textbook PDFs there and re-run.")
        print(f"       See {books_dir / 'README.md'} for which books to use.")
        if args.dry_run:
            print("\nDry run with 0 PDFs — nothing to show.")
        sys.exit(0)

    print(f"Found {len(pdf_paths)} PDF(s) in {books_dir}:")
    for p in pdf_paths:
        size_mb = p.stat().st_size / 1_048_576
        print(f"  - {p.name} ({size_mb:.1f} MB)")

    if args.dry_run:
        dry_run(pdf_paths)
    else:
        full_run(pdf_paths)


if __name__ == "__main__":
    main()
