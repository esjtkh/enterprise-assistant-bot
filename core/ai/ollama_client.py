import os
import ollama
from ai.prompts import SYSTEM_PROMPT, RAG_SYSTEM_PROMPT

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class OllamaClient:

    def __init__(self, model: str = None, host: str = None):
        self.model = model or DEFAULT_MODEL
        self.client = ollama.AsyncClient(host=host or DEFAULT_HOST)

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

        response = await self.client.chat(
            model=self.model,
            messages=messages,
        )

        return response.message.content
