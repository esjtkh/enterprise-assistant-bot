"""ساخت/به‌روزرسانی vector store از تمام chunk های آماده (خروجی
chunk_forum_data.py، یک فایل به‌ازای هر زیرفوروم): برای هر chunk با مدل
embedding لوکال (Ollama) بردار می‌سازد و در ChromaDB ذخیره می‌کند. این index
توسط RAGManager در زمان اجرای ربات خوانده می‌شود.

از upsert استفاده می‌شود (نه پاک‌سازی کامل collection) تا اجرای این اسکریپت
برای یک زیرفوروم جدید، داده‌ی زیرفوروم‌های قبلاً ایندکس‌شده را از بین نبرد؛
اجرای دوباره روی همان فایل هم بی‌خطر است (chunk id ثابت = جایگزینی، نه تکرار).

اجرا: python -m ai.ingestion.build_vector_store
ورودی: core/ai/ingestion/data/*_chunks.jsonl
خروجی: core/ai/vector_store/ (پوشه‌ی persistent chromadb)
"""

import glob
import json
import os

import chromadb
import ollama

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_store")

COLLECTION_NAME = "voron_forum"
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

BATCH_SIZE = 50


def load_chunks(path: str) -> list:
    chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def embed_texts(client: ollama.Client, texts: list) -> list:
    vectors = []
    for text in texts:
        response = client.embeddings(model=EMBED_MODEL, prompt=text)
        vectors.append(response["embedding"])
    return vectors


def index_file(collection, ollama_client, path: str):
    chunks = load_chunks(path)
    print(f"  {os.path.basename(path)}: {len(chunks)} chunks")

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start:batch_start + BATCH_SIZE]

        ids = [c["id"] for c in batch]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        embeddings = embed_texts(ollama_client, texts)

        # upsert نه add: اگر این فایل قبلاً ایندکس شده بود، جایگزین می‌کند
        # نه اینکه رکورد تکراری بسازد یا خطای id-duplicate بدهد.
        collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

        done = batch_start + len(batch)
        print(f"    indexed {done}/{len(chunks)}")


def main():
    chunk_files = sorted(glob.glob(os.path.join(DATA_DIR, "*_chunks.jsonl")))

    if not chunk_files:
        print(f"no *_chunks.jsonl files found in {DATA_DIR}")
        return

    print(f"found {len(chunk_files)} chunk files")

    ollama_client = ollama.Client(host=OLLAMA_HOST)

    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)

    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    for path in chunk_files:
        index_file(collection, ollama_client, path)

    print(f"done. vector store at {VECTOR_STORE_DIR}, collection '{COLLECTION_NAME}', {collection.count()} vectors")


if __name__ == "__main__":
    main()
