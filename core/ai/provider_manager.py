import json
import os

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "provider_state.json")

VALID_PROVIDERS = ("local", "api")
DEFAULT_PROVIDER = os.getenv("AI_DEFAULT_PROVIDER", "local")


class ProviderManager:
    """تعیین می‌کند AIController فعلاً از مدل لوکال (Ollama) استفاده کند یا API (AvalAI).
    این انتخاب با دستور ادمین در ربات تغییر می‌کند و روی دیسک ذخیره می‌شود تا با
    ری‌استارت ربات از بین نرود."""

    def __init__(self):
        self._provider = self._load()

    def _load(self) -> str:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    provider = json.load(f).get("provider")
                    if provider in VALID_PROVIDERS:
                        return provider
            except (json.JSONDecodeError, OSError):
                pass

        return DEFAULT_PROVIDER if DEFAULT_PROVIDER in VALID_PROVIDERS else "local"

    def get(self) -> str:
        return self._provider

    def set(self, provider: str):
        if provider not in VALID_PROVIDERS:
            raise ValueError(f"provider نامعتبر: {provider} (باید یکی از {VALID_PROVIDERS} باشد)")

        self._provider = provider

        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"provider": provider}, f, ensure_ascii=False)
