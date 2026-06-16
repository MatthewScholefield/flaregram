"""Tests for the Telegram API client."""

from __future__ import annotations

import httpx
import pytest
import respx

from flaregram.client import TelegramClient, TelegramError, timestamp
from flaregram.models import BotInfo, Chat, Message, Update, User

TOKEN = "123456:ABC-DEF"
BASE = "https://api.telegram.org"


def _url(method: str) -> str:
    return f"{BASE}/bot{TOKEN}/{method}"


@respx.mock
def test_get_me():
    respx.get(_url("getMe")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "id": 42,
                    "is_bot": True,
                    "first_name": "TestBot",
                    "username": "testbot",
                },
            },
        )
    )
    client = TelegramClient(TOKEN)
    info = client.get_me()
    assert isinstance(info, BotInfo)
    assert info.user.id == 42
    assert info.user.display_name == "TestBot"
    assert info.user.mention == "@testbot"


@respx.mock
def test_send_message():
    respx.get(_url("sendMessage")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 7,
                    "date": 1700000000,
                    "chat": {
                        "id": 555,
                        "type": "private",
                        "first_name": "Alice",
                    },
                    "from": {"id": 42, "is_bot": True, "first_name": "Bot"},
                    "text": "Hello!",
                },
            },
        )
    )
    msg = TelegramClient(TOKEN).send_message(555, "Hello!")
    assert isinstance(msg, Message)
    assert msg.message_id == 7
    assert msg.body == "Hello!"
    assert msg.chat.id == 555
    assert msg.sender is not None and msg.sender.is_bot


@respx.mock
def test_send_message_sends_bool_params_lowercased():
    route = respx.get(_url("sendMessage")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 1,
                    "date": 1,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": True, "first_name": "B"},
                    "text": "x",
                },
            },
        )
    )
    TelegramClient(TOKEN).send_message(
        1, "x", disable_notification=True
    )
    assert route.calls.last.request.url.params["disable_notification"] == "true"


@respx.mock
def test_get_updates_parses_messages():
    respx.get(_url("getUpdates")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "message_id": 10,
                            "date": 1700000000,
                            "chat": {"id": 100, "type": "private", "first_name": "A"},
                            "from": {"id": 100, "is_bot": False, "first_name": "A"},
                            "text": "hi",
                        },
                    },
                    {"update_id": 2},
                ],
            },
        )
    )
    updates = TelegramClient(TOKEN).get_updates()
    assert len(updates) == 2
    assert updates[0].message is not None
    assert updates[0].message.body == "hi"
    assert updates[0].message.sender is not None
    assert updates[1].message is None


@respx.mock
def test_get_chat():
    respx.get(_url("getChat")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "id": 9,
                    "type": "group",
                    "title": "My Group",
                },
            },
        )
    )
    chat = TelegramClient(TOKEN).get_chat(9)
    assert isinstance(chat, Chat)
    assert chat.display_name == "My Group"


@respx.mock
def test_api_error_raises():
    respx.get(_url("getMe")).mock(
        return_value=httpx.Response(
            200, json={"ok": False, "description": "Unauthorized"}
        )
    )
    with pytest.raises(TelegramError, match="Unauthorized"):
        TelegramClient(TOKEN).get_me()


@respx.mock
def test_network_error_raises():
    respx.get(_url("getMe")).mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(TelegramError, match="Network error"):
        TelegramClient(TOKEN).get_me()


def test_empty_token_raises():
    with pytest.raises(TelegramError):
        TelegramClient("")


def test_timestamp_format():
    assert timestamp(1700000000)
    assert timestamp(None) == ""


def test_user_display_names():
    u = User(id=1, is_bot=False, first_name="A", last_name="B", username="ab")
    assert u.display_name == "A B"
    assert u.mention == "@ab"
    u2 = User(id=2, is_bot=False, first_name="Solo")
    assert u2.mention == "Solo"


def test_chat_fallback_names():
    c = Chat(id=5, type="private")
    assert c.display_name == "Chat 5"
    c2 = Chat(id=6, type="channel", username="news")
    assert c2.display_name == "@news"


def test_message_body_falls_back_to_caption():
    m = Message.from_api(
        {
            "message_id": 1,
            "date": 1,
            "chat": {"id": 1, "type": "private"},
            "caption": "a caption",
        }
    )
    assert m.body == "a caption"
    assert m.sender is None


def test_update_without_message():
    u = Update.from_api({"update_id": 99})
    assert u.update_id == 99
    assert u.message is None
