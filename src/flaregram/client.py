"""Thin client for the Telegram Bot HTTP API."""

from __future__ import annotations

import time

import httpx

from .models import BotInfo, Chat, Message, Update

API_BASE = "https://api.telegram.org"
DEFAULT_TIMEOUT = 30.0


class TelegramError(Exception):
    """Raised when the Telegram API returns an error response."""


class TelegramClient:
    """Minimal synchronous client wrapping the Telegram Bot API."""

    def __init__(
        self, token: str, *, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
        if not token:
            raise TelegramError("A bot token is required.")
        self.token = token
        self._base = f"{API_BASE}/bot{token}"
        self._timeout = timeout

    # -- low level -------------------------------------------------------

    def _request(self, method: str, **params) -> dict:
        try:
            resp = httpx.get(
                f"{self._base}/{method}",
                params=_clean(params),
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise TelegramError(f"Network error: {exc}") from exc
        try:
            payload = resp.json()
        except ValueError as exc:
            raise TelegramError(
                f"Could not decode response: {resp.text!r}"
            ) from exc
        if not payload.get("ok"):
            desc = payload.get("description", "Unknown error")
            raise TelegramError(desc)
        return payload["result"]

    # -- bot -------------------------------------------------------------

    def get_me(self) -> BotInfo:
        return BotInfo.from_api(self._request("getMe"))

    # -- updates ---------------------------------------------------------

    def get_updates(
        self,
        *,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = 0,
    ) -> list[Update]:
        result = self._request(
            "getUpdates",
            offset=offset,
            limit=limit,
            timeout=timeout,
            allowed_updates='["message","edited_message"]',
        )
        return [Update.from_api(u) for u in result]

    # -- messaging -------------------------------------------------------

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        reply_to: int | None = None,
        parse_mode: str | None = None,
        disable_notification: bool = False,
    ) -> Message:
        result = self._request(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )
        return Message.from_api(result)

    def get_chat(self, chat_id: int | str) -> Chat:
        return Chat.from_api(self._request("getChat", chat_id=chat_id))


def _clean(params: dict) -> dict:
    """Drop ``None`` values and stringify bools for query params."""
    cleaned: dict = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cleaned[key] = str(value).lower()
        else:
            cleaned[key] = value
    return cleaned


def timestamp(ts: int | None) -> str:
    """Render a Unix timestamp as a readable local string."""
    if not ts:
        return ""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
