import datetime

# تعداد پیام‌های قبلی (سوال+جواب) که به‌عنوان تاریخچه به مدل داده می‌شود. عدد
# بالاتر یعنی حافظه‌ی بهتر ولی پرامپت بزرگ‌تر (کندتر و برای provider api
# گران‌تر).
MAX_TURNS = 10


class ConversationHistory:
    """تاریخچه‌ی مکالمه‌ی هر کاربر را فقط در حافظه (RAM) نگه می‌دارد — با
    ری‌استارت ربات از بین می‌رود و هر شب نیمه‌شب توسط main.py کامل پاک
    می‌شود (نه به‌ازای هر کاربر جدا). مستقل از provider (local/api) است تا
    اگر کاربر وسط مکالمه provider را عوض کند، تاریخچه قطع نشود."""

    def __init__(self):
        self._history: dict[int, list[dict]] = {}

    def get(self, user_id: int) -> list:
        return self._history.get(user_id, [])

    def append(self, user_id: int, role: str, content: str):
        turns = self._history.setdefault(user_id, [])
        turns.append({"role": role, "content": content})

        # نگه‌داشتن فقط MAX_TURNS پیام آخر (کاربر+دستیار با هم شمرده می‌شوند)
        max_messages = MAX_TURNS * 2
        if len(turns) > max_messages:
            del turns[: len(turns) - max_messages]

    def clear_user(self, user_id: int):
        self._history.pop(user_id, None)

    def clear_all(self):
        self._history.clear()
