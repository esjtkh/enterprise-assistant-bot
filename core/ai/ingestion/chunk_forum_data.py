"""تبدیل تمام thread های خام JSONL (خروجی scrape_voron_forum.py، یک فایل به‌ازای
هر زیرفوروم) به chunk های آماده‌ی embedding — هر chunk با متادیتای کامل (عنوان،
URL، نویسنده، تاریخ، نام زیرفوروم) تا در پاسخ RAG بتوان منبع را نشان داد.

اجرا: python -m ai.ingestion.chunk_forum_data
ورودی: core/ai/ingestion/data/*.jsonl (هر فایل = یک زیرفوروم، به‌جز خروجی این
        اسکریپت خودش که با پسوند _chunks.jsonl مشخص است)
خروجی: core/ai/ingestion/data/{same_name}_chunks.jsonl (یک فایل chunk جدا
        به‌ازای هر فایل ورودی، تا اسکریپت بعدی بداند کدام‌ها را تازه ایندکس کند)
"""

import glob
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# پست‌های کوتاه‌تر از این آستانه به‌تنهایی context کافی ندارند (مثلاً "ممنون!")
# و با پست قبلی/بعدی همان thread ادغام می‌شوند.
MIN_CHUNK_CHARS = 200

# پست‌های طولانی (راهنماهای فنی مفصل) به قطعات با این حداکثر طول شکسته می‌شوند
MAX_CHUNK_CHARS = 1500
CHUNK_OVERLAP_CHARS = 150


def clean_post_text(text: str) -> str:
    """خط‌های quote خام فروم (مثل 'username said:') که خودِ XenForo تکرار
    می‌کند و برای embedding نویز اضافه می‌کنند را حذف نمی‌کند — نگه داشته
    می‌شوند چون معنا می‌دهند (نشان می‌دهند پاسخ به کدام حرف است)، فقط
    whitespace اضافه پاکسازی می‌شود."""

    return re.sub(r"\n{3,}", "\n\n", text.strip())


def split_long_text(text: str) -> list:
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    parts = []
    start = 0

    while start < len(text):
        end = start + MAX_CHUNK_CHARS
        parts.append(text[start:end])
        start = end - CHUNK_OVERLAP_CHARS

    return parts


def merge_short_posts(posts: list) -> list:
    """پست‌های کوتاه را با پست بعدی ادغام می‌کند تا هر واحد نهایی معنای
    مستقلی داشته باشد؛ نویسنده/تاریخ گروه بر اساس اولین پست ثبت می‌شود."""

    merged = []
    buffer_posts = []

    def flush():
        if not buffer_posts:
            return
        merged.append({
            "authors": [p["author"] for p in buffer_posts],
            "date": buffer_posts[0]["date"],
            "text": "\n\n".join(p["text"] for p in buffer_posts),
        })
        buffer_posts.clear()

    for post in posts:
        buffer_posts.append(post)
        combined_len = sum(len(p["text"]) for p in buffer_posts)

        if combined_len >= MIN_CHUNK_CHARS:
            flush()

    flush()  # باقیمانده‌ی کوتاه انتهای thread هم به‌عنوان آخرین گروه ذخیره شود

    return merged


def build_chunks(thread: dict, source: str) -> list:
    chunks = []
    groups = merge_short_posts(thread["posts"])

    for group_idx, group in enumerate(groups):
        text = clean_post_text(group["text"])
        pieces = split_long_text(text)

        for piece_idx, piece in enumerate(pieces):
            chunk_id = f"{thread['url']}#g{group_idx}-p{piece_idx}"

            chunks.append({
                "id": chunk_id,
                "text": f"موضوع: {thread['title']}\n\n{piece}",
                "metadata": {
                    "thread_title": thread["title"],
                    "thread_url": thread["url"],
                    "authors": ", ".join(group["authors"]),
                    "date": group["date"] or "",
                    "source": source,
                },
            })

    return chunks


def chunk_file(input_path: str) -> str:
    basename = os.path.basename(input_path)
    source = basename[:-len(".jsonl")]
    output_path = os.path.join(DATA_DIR, f"{source}_chunks.jsonl")

    total_chunks = 0

    with open(input_path, encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for line in infile:
            thread = json.loads(line)

            if not thread["posts"]:
                continue

            for chunk in build_chunks(thread, source):
                outfile.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_chunks += 1

    print(f"  {basename} -> {total_chunks} chunks")
    return output_path


def main():
    input_files = [
        f for f in glob.glob(os.path.join(DATA_DIR, "*.jsonl"))
        if not os.path.basename(f).endswith("_chunks.jsonl")
    ]

    if not input_files:
        print(f"no *.jsonl thread files found in {DATA_DIR}")
        return

    print(f"found {len(input_files)} thread files")

    for input_path in sorted(input_files):
        chunk_file(input_path)

    print("done.")


if __name__ == "__main__":
    main()
