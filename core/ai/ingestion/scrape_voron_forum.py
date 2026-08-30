"""اسکریپت مستقل (نه بخشی از ربات runtime) برای استخراج thread های زیرفوروم‌های
فنی/ساخت فروم Voron Design و ذخیره‌شان به‌عنوان اسناد خام JSON — ورودی مرحله‌ی
بعدی (chunking + embedding) برای RAG.

اجرا: python -m ai.ingestion.scrape_voron_forum
خروجی: core/ai/ingestion/data/{forum_slug}.jsonl (هر خط یک thread کامل، یک
فایل جدا به‌ازای هر زیرفوروم — اگر یکی fail شد بقیه دست‌نخورده می‌مانند)

سایت پشت یک بررسی ضدبات JS-only است، به همین دلیل به‌جای httpx/requests از
Playwright (مرورگر headless واقعی) استفاده شده.
"""

import asyncio
import json
import os
import re

from playwright.async_api import async_playwright

BASE_URL = "https://forum.vorondesign.com"

# زیرفوروم‌های فنی/ساخت — voron-trident قبلاً جدا اسکرپ و ایندکس شده، اینجا
# نیست تا دوباره گرفته نشود. off-topic/marketplace/announcements هم عمداً
# اینجا نیستند چون محتوای فنی قابل استفاده در RAG کم دارند.
FORUM_SLUGS = [
    "voron-v2-x.11",
    "voron-zero.12",
    "voron-switchwire.13",
    "voron-legacy.14",
    "afterburner-and-stealthburner.15",
    "voron-extruders.16",
    "voron-tap.48",
    "electronics.19",
    "slice-and-print.18",
    "filament.20",
    "documentation.25",
    "kits.24",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# فاصله بین درخواست‌ها برای رعایت ادب نسبت به سرور فروم (rate limiting دستی)
REQUEST_DELAY_SECONDS = 1.5

THREAD_LINK_RE = re.compile(r"^/threads/[^/]+\.\d+/$")


async def _new_page(browser):
    return await browser.new_page(user_agent=USER_AGENT)


async def _goto(page, url: str):
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(2500)  # مهلت عبور از بررسی ضدبات JS


async def get_forum_page_count(page, forum_url: str) -> int:
    await _goto(page, forum_url)

    slug_path = forum_url.replace(BASE_URL, "").rstrip("/")

    last_page_links = await page.eval_on_selector_all(
        f"a[href*='{slug_path}/page-']",
        "els => els.map(e => e.getAttribute('href'))",
    )

    max_page = 1
    for href in last_page_links:
        match = re.search(r"page-(\d+)", href)
        if match:
            max_page = max(max_page, int(match.group(1)))

    return max_page


async def collect_thread_urls(page, forum_url: str, page_count: int) -> list:
    thread_urls = []
    seen = set()

    for page_num in range(1, page_count + 1):
        url = forum_url if page_num == 1 else f"{forum_url}page-{page_num}"
        await _goto(page, url)

        hrefs = await page.eval_on_selector_all(
            "a[href^='/threads/']",
            "els => els.map(e => e.getAttribute('href'))",
        )

        for href in hrefs:
            clean = href.split("?")[0]
            if not clean.endswith("/"):
                clean += "/"

            if THREAD_LINK_RE.match(clean) and clean not in seen:
                seen.add(clean)
                thread_urls.append(f"{BASE_URL}{clean}")

        print(f"  [list] page {page_num}/{page_count}: {len(thread_urls)} threads so far")
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    return thread_urls


async def get_thread_page_count(page) -> int:
    hrefs = await page.eval_on_selector_all(
        "a.pageNav-page",
        "els => els.map(e => e.textContent.trim())",
    )

    numbers = [int(h) for h in hrefs if h.isdigit()]
    return max(numbers) if numbers else 1


async def scrape_thread(page, thread_url: str) -> dict:
    await _goto(page, thread_url)

    title = (await page.title()).replace(" | VORON Design", "").strip()
    page_count = await get_thread_page_count(page)

    posts = []

    for page_num in range(1, page_count + 1):
        url = thread_url if page_num == 1 else f"{thread_url}page-{page_num}"

        if page_num > 1:
            await _goto(page, url)

        post_handles = await page.query_selector_all("article.message--post")

        for handle in post_handles:
            username_el = await handle.query_selector(".message-name .username")
            username = (await username_el.inner_text()).strip() if username_el else "ناشناس"

            date_el = await handle.query_selector("time")
            date = await date_el.get_attribute("datetime") if date_el else None

            body_el = await handle.query_selector(".bbWrapper")
            body = (await body_el.inner_text()).strip() if body_el else ""

            if body:
                posts.append({"author": username, "date": date, "text": body})

        if page_num < page_count:
            await asyncio.sleep(REQUEST_DELAY_SECONDS)

    return {"url": thread_url, "title": title, "posts": posts}


def _output_paths(slug: str):
    base = os.path.join(OUTPUT_DIR, slug.split(".")[0].replace("-", "_"))
    return f"{base}.jsonl", f"{base}.done"


async def scrape_forum(page, slug: str):
    output_file, done_marker = _output_paths(slug)

    print(f"=== {slug} ===")

    page_count = await get_forum_page_count(page, f"{BASE_URL}/forums/{slug}/")
    print(f"  {page_count} listing pages")

    thread_urls = await collect_thread_urls(page, f"{BASE_URL}/forums/{slug}/", page_count)
    print(f"  {len(thread_urls)} threads total")

    with open(output_file, "w", encoding="utf-8") as f:
        for i, thread_url in enumerate(thread_urls, 1):
            try:
                thread = await scrape_thread(page, thread_url)
            except Exception as e:
                print(f"  [{i}/{len(thread_urls)}] FAILED {thread_url}: {e}")
                continue

            f.write(json.dumps(thread, ensure_ascii=False) + "\n")
            f.flush()

            print(f"  [{i}/{len(thread_urls)}] saved: {thread['title']} ({len(thread['posts'])} posts)")
            await asyncio.sleep(REQUEST_DELAY_SECONDS)

    # این فایل فقط بعد از اتمام کامل زیرفوروم نوشته می‌شود — نشانه‌ی این‌که
    # output_file معتبر و کامل است، نه ناقص (مثلاً به‌خاطر توقف دستی وسط کار).
    # اجرای بعدی اسکریپت با همین نشانه تشخیص می‌دهد کدام زیرفوروم‌ها را باید
    # دوباره (از صفر) بگیرد.
    with open(done_marker, "w", encoding="utf-8") as f:
        f.write(f"{len(thread_urls)} threads\n")

    print(f"  done: {output_file}")


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # زیرفوروم‌هایی که از اجرای قبلی ناقص مانده‌اند (فایل jsonl هست ولی
    # marker .done نیست) پاک می‌شوند تا از صفر و کامل دوباره گرفته شوند —
    # چون نمی‌دانیم دقیقاً کجای لیست thread ها متوقف شده بود.
    for slug in FORUM_SLUGS:
        output_file, done_marker = _output_paths(slug)
        if os.path.exists(output_file) and not os.path.exists(done_marker):
            print(f"removing incomplete data for {slug} (will re-scrape from scratch)")
            os.remove(output_file)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await _new_page(browser)

        for slug in FORUM_SLUGS:
            _, done_marker = _output_paths(slug)

            if os.path.exists(done_marker):
                print(f"skip {slug} (already done)")
                continue

            try:
                await scrape_forum(page, slug)
            except Exception as e:
                print(f"FORUM FAILED {slug}: {e}")
                continue

        await browser.close()

    print("all forums done.")


if __name__ == "__main__":
    asyncio.run(main())
