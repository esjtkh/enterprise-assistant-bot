import os
from openai import AsyncOpenAI
from ai.prompts import SYSTEM_PROMPT, RAG_SYSTEM_PROMPT

BASE_URL = "https://api.avalai.ir/v1"
DEFAULT_MODEL = os.getenv("AVALAI_MODEL", "gpt-5.5")


class AvalAIClient:
    """کلاینت API سرویس AvalAI (پروکسی سازگار با OpenAI برای مدل‌های مختلف) —
    همان اینترفیس OllamaClient (ask) را پیاده‌سازی می‌کند تا AIController بدون
    تغییر بین provider ها سوییچ کند.
    توجه: با استفاده از این کلاینت، prompt کاربر به سرور AvalAI ارسال می‌شود."""

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or DEFAULT_MODEL

        key = api_key or os.getenv("AVALAI_API_KEY")
        if not key:
            raise RuntimeError("AVALAI_API_KEY در .env تنظیم نشده است.")

        self.client = AsyncOpenAI(api_key=key, base_url=BASE_URL)

    async def ask(self, prompt: str, context: str = "", history: list = None) -> str:

        if context:
            system = RAG_SYSTEM_PROMPT
            user_content = f"اطلاعات مرتبط:\n{context}\n\nسوال:\n{prompt}"
        else:
            system = SYSTEM_PROMPT
            user_content = prompt

        messages = [{"role": "system", "content": system}]
        messages.extend(history or [])
        messages.append({"role": "user", "content": user_content})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        return response.choices[0].message.content
