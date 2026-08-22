"""Browser-backed authentication state for Streamlit.

Streamlit clears ``session_state`` on a hard browser refresh.  This lightweight
cookie only stores the short-lived JWT; the app validates it with ``/auth/me``
before using it and removes it immediately if it has expired or is invalid.
"""

from datetime import datetime, timedelta, timezone

import extra_streamlit_components as stx

COOKIE_NAME = "rag_chat_access_token"
COOKIE_LIFETIME_DAYS = 7


def create_cookie_manager():
    return stx.CookieManager(key="rag-chat-cookie-manager")


def load_token(cookie_manager) -> str | None:
    return cookie_manager.get(cookie=COOKIE_NAME)


def save_token(cookie_manager, token: str) -> None:
    cookie_manager.set(
        cookie=COOKIE_NAME,
        val=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=COOKIE_LIFETIME_DAYS),
        key="save-rag-chat-token",
    )


def clear_token(cookie_manager) -> None:
    # CookieManager calls JavaScript deletion before updating its local cache.
    # On a freshly restored session that cache can already be empty, in which
    # case its internal ``del`` raises KeyError. The browser delete has still
    # been requested, and logout must always continue.
    try:
        cookie_manager.delete(cookie=COOKIE_NAME, key="delete-rag-chat-token")
    except KeyError:
        pass
