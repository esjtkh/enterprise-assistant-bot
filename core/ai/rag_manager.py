import logging
import os
from dataclasses import dataclass
from enum import Enum

import chromadb
import ollama

logger = logging.getLogger(__name__)


class RAGStatus(Enum):
    HIT = "hit"                # قطعه‌ی مرتبط زیر MAX_DISTANCE — مدل جواب می‌دهد
    WEAK = "weak"              # نتیجه‌ای بین MAX_DISTANCE و HARD_MAX_DISTANCE —
                              # مدل جواب نمی‌سازد، فقط لینک threadها نشان داده می‌شود
    NO_MATCH = "no_match"      # هیچ نتیجه‌ای زیر HARD_MAX_DISTANCE نبود
    UNAVAILABLE = "unavailable"  # جستجو اصلاً ممکن نشد (Ollama خاموش / ایندکس نیست)


@dataclass
class RAGSource:
    title: str
    url: str
    distance: float


@dataclass
class RAGResult:
    status: RAGStatus
    context: str = ""
    closest_distance: float | None = None
    # فقط برای WEAK پر می‌شود: threadهای احتمالاً مرتبط که به کاربر نشان داده می‌شوند
    weak_sources: list = None

VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_store")
COLLECTION_NAME = "voron_forum"

EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
# مدل ترجمه عمداً از مدل چت اصلی جدا نگه داشته شده (نه از OllamaClient گرفته
# می‌شود) — این یک کار کوچک و ارزان است که همیشه باید لوکال و سریع اجرا شود،
# حتی وقتی provider سراسری روی api (AvalAI) است.
TRANSLATE_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

TOP_K = 5

TRANSLATE_PROMPT = """Translate the following text to English. This forum data is in
English, so the query must be in English to match well via embedding search.
If the text is already in English, return it unchanged.
Output ONLY the translated text, nothing else — no quotes, no explanation.

Text: {text}"""

# cosine distance (نه similarity) — هرچه کمتر یعنی نزدیک‌تر. با تست دستی روی
# nomic-embed-text: سوالات واقعاً مرتبط با محتوای ایندکس‌شده معمولاً فاصله‌ی
# ۰.۲۵–۰.۳۲ دارند؛ سوالات بی‌ربط (مثل "سلام خوبی؟") به بالای ۰.۴۰ می‌رسند.
# با RAG_MAX_DISTANCE در .env قابل تنظیم است. برای کالیبره کردن:
#   python -m ai.ingestion.check_rag_distance "سوال نمونه"
MAX_DISTANCE = float(os.getenv("RAG_MAX_DISTANCE", "0.35"))

# نتایج بین MAX_DISTANCE و HARD_MAX_DISTANCE «ضعیف» تلقی می‌شوند: مدل روی آن‌ها
# جواب نمی‌سازد (خطر توهم)، اما لینک threadها به کاربر نشان داده می‌شود تا خودش
# قضاوت کند. بالاتر از HARD_MAX_DISTANCE کلاً نادیده گرفته می‌شود.
HARD_MAX_DISTANCE = float(os.getenv("RAG_HARD_MAX_DISTANCE", "0.42"))


class RAGManager:
    """جستجوی شباهت روی اسناد ایندکس‌شده (فعلاً thread های زیرفوروم‌های فنی
    فروم Voron Design — core/ai/ingestion/) و برگرداندن نزدیک‌ترین قطعات متن
    به‌عنوان context برای مدل. ایندکس با اسکریپت‌های core/ai/ingestion/ ساخته
    می‌شود، نه در زمان اجرای ربات."""

    def __init__(self):
        self._collection = None
        self._embed_client = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        if not os.path.isdir(VECTOR_STORE_DIR):
            logger.warning("RAG: vector store پیدا نشد (%s) — RAG غیرفعال است.", VECTOR_STORE_DIR)
            return None

        chroma_client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)

        try:
            self._collection = chroma_client.get_collection(COLLECTION_NAME)
        except Exception as e:
            logger.warning("RAG: باز کردن collection «%s» ناموفق بود: %s", COLLECTION_NAME, e)
            return None

        return self._collection

    def _get_embed_client(self):
        if self._embed_client is None:
            self._embed_client = ollama.Client(host=OLLAMA_HOST)
        return self._embed_client

    async def _translate_to_english(self, text: str) -> str:
        """سوال را قبل از embedding به انگلیسی برمی‌گرداند — چون محتوای
        ایندکس‌شده (فروم Voron) انگلیسی است و embedding چندزبانه‌ی محدود
        nomic-embed-text باعث می‌شود سوال فارسی فاصله‌ی cosine بزرگ‌تری از
        chunk های مرتبط بگیرد. اگر ترجمه شکست بخورد، متن اصلی برگردانده
        می‌شود تا جستجو (با کیفیت پایین‌تر) هنوز انجام شود.

        اگر متن از قبل عمدتاً انگلیسی/ASCII است، اصلاً به مدل داده نمی‌شود —
        مدل کوچک لوکال حتی متن انگلیسی را هم گاهی "بازنویسی" می‌کند (مثلاً
        "sensorless homing" را به "sensor-independent alignment" تبدیل کرد)
        و اصطلاحات فنی دقیق فروم را از دست می‌دهد."""

        ascii_ratio = sum(1 for ch in text if ch.isascii()) / max(len(text), 1)
        if ascii_ratio > 0.9:
            return text

        embed_client = self._get_embed_client()

        try:
            response = embed_client.chat(
                model=TRANSLATE_MODEL,
                messages=[{"role": "user", "content": TRANSLATE_PROMPT.format(text=text)}],
            )
            translated = response["message"]["content"].strip()
        except Exception as e:
            logger.warning(
                "RAG: ترجمه‌ی سوال به انگلیسی ناموفق بود (%s: %s) — با متن اصلی جستجو می‌شود.",
                type(e).__name__, e,
            )
            return text

        return translated or text

    async def search(self, prompt: str) -> RAGResult:
        collection = self._get_collection()

        if collection is None:
            return RAGResult(RAGStatus.UNAVAILABLE)

        embed_client = self._get_embed_client()
        query_text = await self._translate_to_english(prompt)

        try:
            query_embedding = embed_client.embeddings(model=EMBED_MODEL, prompt=query_text)["embedding"]
        except Exception as e:
            logger.warning(
                "RAG: ساخت embedding سوال با مدل «%s» روی %s ناموفق بود (%s: %s). "
                "آیا Ollama در حال اجراست؟",
                EMBED_MODEL, OLLAMA_HOST, type(e).__name__, e,
            )
            return RAGResult(RAGStatus.UNAVAILABLE)

        try:
            results = collection.query(query_embeddings=[query_embedding], n_results=TOP_K)
        except Exception as e:
            logger.warning("RAG: کوئری روی vector store ناموفق بود: %s", e)
            return RAGResult(RAGStatus.UNAVAILABLE)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not documents:
            logger.info("RAG: جستجو نتیجه‌ای نداشت.")
            return RAGResult(RAGStatus.NO_MATCH)

        closest = min(distances)

        parts = []          # قطعه‌های زیر MAX_DISTANCE — context برای مدل
        weak = []           # نتایج بین MAX_DISTANCE و HARD_MAX_DISTANCE
        seen_weak_urls = set()

        for doc, meta, distance in zip(documents, metadatas, distances):
            title = meta.get("thread_title", "")
            url = meta.get("thread_url", "")

            if distance <= MAX_DISTANCE:
                parts.append(f"[{title}]({url})\n{doc}")
            elif distance <= HARD_MAX_DISTANCE and url not in seen_weak_urls:
                seen_weak_urls.add(url)
                weak.append(RAGSource(title=title, url=url, distance=distance))

        if parts:
            logger.info(
                "RAG: %d قطعه‌ی مرتبط به context اضافه شد (نزدیک‌ترین فاصله %.3f).",
                len(parts), closest,
            )
            return RAGResult(
                RAGStatus.HIT,
                context="\n\n---\n\n".join(parts),
                closest_distance=closest,
            )

        if weak:
            logger.info(
                "RAG: نتیجه‌ی دقیق نبود ولی %d thread احتمالاً مرتبط پیدا شد "
                "(نزدیک‌ترین فاصله %.3f).",
                len(weak), closest,
            )
            return RAGResult(
                RAGStatus.WEAK,
                closest_distance=closest,
                weak_sources=weak,
            )

        logger.info(
            "RAG: %d نتیجه پیدا شد ولی همه دورتر از HARD_MAX (%.2f) بودند؛ نزدیک‌ترین فاصله %.3f.",
            len(documents), HARD_MAX_DISTANCE, closest,
        )
        return RAGResult(RAGStatus.NO_MATCH, closest_distance=closest)
