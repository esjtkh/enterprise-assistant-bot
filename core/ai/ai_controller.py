from ai.ollama_client import OllamaClient
from ai.provider_manager import ProviderManager
from ai.rag_manager import RAGManager, RAGStatus
from ai.conversation_history import ConversationHistory

# پاسخ ثابت وقتی هیچ منبع مرتبطی پیدا نشد (سوال غیرفنی یا خارج از دامنه‌ی
# منابع). عمداً هیچ فراخوانی به مدل انجام نمی‌شود تا از دانش عمومی/اینترنت
# استفاده نکند.
NO_MATCH_REPLY = (
    "❌ چیزی مرتبط با سوال شما در منابع پیدا نشد.\n"
    "لطفاً فقط سوال فنی (مثلاً درباره‌ی پرینتر سه‌بعدی، تنظیمات، قطعات و ...) بپرسید."
)


def _format_weak_reply(sources) -> str:
    """وقتی نتیجه‌ی دقیقی نبود ولی چند thread احتمالاً مرتبط پیدا شد: مدل جواب
    نمی‌سازد (خطر توهم)، فقط این لینک‌ها را می‌دهیم تا کاربر خودش قضاوت کند."""

    lines = [
        "دربارهٔ این سوال جواب دقیقی در منابع پیدا نشد، اما این بحث‌ها شاید مرتبط باشند:",
        "",
    ]
    for s in sources:
        title = s.title or s.url
        lines.append(f"• [{title}]({s.url})")
    return "\n".join(lines)

# وقتی خودِ RAG در دسترس نیست (Ollama خاموش، ایندکس ساخته نشده و ...).
RAG_UNAVAILABLE_REPLY = (
    "⚠️ سرویس جستجوی منابع در دسترس نیست، بنابراین نمی‌توانم به سوال فنی جواب بدهم. "
    "لطفاً بعداً دوباره تلاش کنید."
)


class AIController:

    def __init__(self):

        self.provider_manager = ProviderManager()
        self.rag = RAGManager()
        self.history = ConversationHistory()

        self._ollama_client = None
        self._avalai_client = None

    def _get_llm_client(self, provider: str = None):
        """کلاینت LLM را برمی‌گرداند؛ اگر provider مشخص شده باشد همون استفاده
        می‌شود (مثلاً برای یک session مکالمه‌ای مخصوص یک کاربر)، وگرنه provider
        سراسری (که با /ai_mode تنظیم می‌شود) ملاک است. ساخت هرکدام تنبل (lazy)
        است تا مثلاً نبودن AVALAI_API_KEY وقتی provider هنوز local است باعث خطا نشود."""

        provider = provider or self.provider_manager.get()

        if provider == "api":

            if self._avalai_client is None:
                from ai.avalai_client import AvalAIClient
                self._avalai_client = AvalAIClient()

            return self._avalai_client

        if self._ollama_client is None:
            self._ollama_client = OllamaClient()

        return self._ollama_client

    async def handle(self, prompt: str, provider: str = None, user_id: int = None) -> str:

        # همیشه اول در منابع ایندکس‌شده (RAGManager) جستجو می‌شود. سیاست فعلی:
        # فقط بر اساس منابع بازیابی‌شده جواب داده می‌شود. اگر منبع مرتبطی زیر
        # آستانه پیدا نشد، اصلاً از مدل سوال نمی‌پرسیم و یک پاسخ ثابت می‌دهیم تا
        # از دانش عمومی/اینترنت استفاده نشود.
        rag = await self.rag.search(prompt)

        if rag.status is RAGStatus.UNAVAILABLE:
            return RAG_UNAVAILABLE_REPLY

        if rag.status is RAGStatus.NO_MATCH:
            if user_id is not None:
                self.history.append(user_id, "user", prompt)
                self.history.append(user_id, "assistant", NO_MATCH_REPLY)
            return NO_MATCH_REPLY

        if rag.status is RAGStatus.WEAK:
            reply = _format_weak_reply(rag.weak_sources)
            if user_id is not None:
                self.history.append(user_id, "user", prompt)
                self.history.append(user_id, "assistant", reply)
            return reply

        llm = self._get_llm_client(provider)

        # تاریخچه فقط وقتی user_id داده شده باشد استفاده می‌شود (یعنی از
        # session مکالمه‌ای /ai صدا زده شده)؛ برای فراخوانی‌های بی‌حالت
        # (مثلاً /ai <سوال> یک‌باره) بی‌تاثیر می‌ماند.
        history = self.history.get(user_id) if user_id is not None else None

        answer = await llm.ask(prompt, context=rag.context, history=history)

        if user_id is not None:
            self.history.append(user_id, "user", prompt)
            self.history.append(user_id, "assistant", answer)

        return answer

    def set_provider(self, provider: str):
        """provider را عوض می‌کند؛ برای api همین‌جا کلید API را اعتبارسنجی می‌کند
        تا ادمین فوراً بفهمد نه اینکه کاربر بعداً وسط سوال با خطا مواجه شود."""

        if provider == "api":
            from ai.avalai_client import AvalAIClient
            self._avalai_client = AvalAIClient()

        self.provider_manager.set(provider)

    def get_provider(self) -> str:
        return self.provider_manager.get()

    def validate_provider(self, provider: str):
        """می‌سازد (و برای استفاده‌های بعدی cache می‌کند) اما provider سراسری
        را عوض نمی‌کند؛ برای اعتبارسنجی قبل از شروع یک session مخصوص کاربر."""

        self._get_llm_client(provider)
