"""ابزار کالیبره کردن آستانه‌ی RAG.

برای هر سوالی که به‌عنوان آرگومان بدهی، جستجو را انجام می‌دهد و فاصله‌ی
cosine و عنوان ۵ نزدیک‌ترین chunk را چاپ می‌کند — تا ببینی آستانه‌ی مناسب
(RAG_MAX_DISTANCE) چقدر است.

نمونه:
    python -m ai.ingestion.check_rag_distance "چطور sensorless homing را تنظیم کنم؟" "سلام خوبی؟"

اگر آرگومانی ندهی، از چند سوال پیش‌فرض (فنی و غیرفنی) استفاده می‌شود.
"""

import asyncio
import sys

from ai.rag_manager import (
    RAGManager,
    MAX_DISTANCE,
    HARD_MAX_DISTANCE,
    TOP_K,
    EMBED_MODEL,
)

DEFAULT_QUERIES = [
    # انتظار: مرتبط (فاصله‌ی کم)
    "چطور sensorless homing را روی Voron 2.4 تنظیم کنم؟",
    "z offset را چطور کالیبره کنم؟",
    "input shaper در klipper",
    "دمای مناسب برای چاپ ABS",
    # انتظار: نامرتبط (فاصله‌ی زیاد)
    "سلام خوبی؟",
    "پایتخت فرانسه کجاست؟",
]


async def main(queries):
    rag = RAGManager()
    collection = rag._get_collection()

    if collection is None:
        print("collection در دسترس نیست (Ollama/ایندکس را بررسی کن).")
        return

    print(f"MAX_DISTANCE = {MAX_DISTANCE}  |  HARD_MAX_DISTANCE = {HARD_MAX_DISTANCE}")
    print("  ✓ = جواب مدل   ~ = فقط لینک (ضعیف)   ✗ = نادیده\n")

    for q in queries:
        query_text = await rag._translate_to_english(q)
        try:
            emb = rag._get_embed_client().embeddings(
                model=EMBED_MODEL, prompt=query_text,
            )["embedding"]
        except Exception as e:
            print(f"[embedding ناموفق: {e}] — Ollama در حال اجراست؟")
            return

        res = collection.query(query_embeddings=[emb], n_results=TOP_K)
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]

        print(f"سوال: {q}")
        if query_text.strip() != q.strip():
            print(f"  (ترجمه: {query_text})")
        for d, m in zip(dists, metas):
            if d <= MAX_DISTANCE:
                mark = "✓"
            elif d <= HARD_MAX_DISTANCE:
                mark = "~"
            else:
                mark = "✗"
            print(f"  [{mark}] {d:.3f}  {m.get('thread_title', '')[:70]}")
        print()


if __name__ == "__main__":
    qs = sys.argv[1:] or DEFAULT_QUERIES
    asyncio.run(main(qs))
