import os

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# آی‌دی کاربرانی که با رمز درست وارد بخش مدیریت شده‌اند (فقط در حافظه؛ با
# ری‌استارت ربات پاک می‌شود و باید دوباره وارد شوند — رفتار طبیعی یک login)
_authenticated_admins = set()


def try_login(user_id: int, password: str) -> bool:
    if not ADMIN_PASSWORD:
        return False

    if password == ADMIN_PASSWORD:
        _authenticated_admins.add(user_id)
        return True

    return False


def is_admin(user_id: int) -> bool:
    return user_id in _authenticated_admins


def logout(user_id: int):
    _authenticated_admins.discard(user_id)
