"""End-to-end tests for the CLI commands via Typer's CliRunner."""

from __future__ import annotations

import json

import httpx
import respx
from typer.testing import CliRunner

from tgtool.cli import app

runner = CliRunner()
TOKEN = "123456:ABC-DEF"
BASE = "https://api.telegram.org"


def _url(method: str) -> str:
    return f"{BASE}/bot{TOKEN}/{method}"


@respx.mock
def test_me_human():
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
    result = runner.invoke(app, ["me", "--token", TOKEN])
    assert result.exit_code == 0, result.output
    assert "TestBot" in result.output
    assert "id=42" in result.output


@respx.mock
def test_me_json():
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
    result = runner.invoke(
        app, ["me", "--token", TOKEN, "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["user"]["id"] == 42
    assert data["user"]["username"] == "testbot"


@respx.mock
def test_error_json_format():
    respx.get(_url("getMe")).mock(
        return_value=httpx.Response(
            200, json={"ok": False, "description": "Unauthorized"}
        )
    )
    result = runner.invoke(
        app, ["me", "--token", TOKEN, "--format", "json"]
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["error"] == "Unauthorized"


@respx.mock
def test_chats_human():
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
                ],
            },
        )
    )
    result = runner.invoke(app, ["chats", "--token", TOKEN])
    assert result.exit_code == 0, result.output
    assert "100" in result.output
    assert "A" in result.output


@respx.mock
def test_chats_dedup():
    respx.get(_url("getUpdates")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "message_id": 1,
                            "date": 1,
                            "chat": {"id": 100, "type": "private", "first_name": "A"},
                            "from": {"id": 100, "is_bot": False, "first_name": "A"},
                            "text": "1",
                        },
                    },
                    {
                        "update_id": 2,
                        "message": {
                            "message_id": 2,
                            "date": 2,
                            "chat": {"id": 100, "type": "private", "first_name": "A"},
                            "from": {"id": 100, "is_bot": False, "first_name": "A"},
                            "text": "2",
                        },
                    },
                ],
            },
        )
    )
    result = runner.invoke(
        app, ["chats", "--token", TOKEN, "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == 100


@respx.mock
def test_send_human():
    respx.get(_url("sendMessage")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 7,
                    "date": 1700000000,
                    "chat": {"id": 555, "type": "private", "first_name": "Alice"},
                    "from": {"id": 42, "is_bot": True, "first_name": "Bot"},
                    "text": "Hello!",
                },
            },
        )
    )
    result = runner.invoke(app, ["send", "555", "Hello!", "--token", TOKEN])
    assert result.exit_code == 0, result.output
    assert "Sent" in result.output
    assert "555" in result.output


@respx.mock
def test_send_json():
    respx.get(_url("sendMessage")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 7,
                    "date": 1700000000,
                    "chat": {"id": 555, "type": "private", "first_name": "Alice"},
                    "from": {"id": 42, "is_bot": True, "first_name": "Bot"},
                    "text": "Hello!",
                },
            },
        )
    )
    result = runner.invoke(
        app, ["send", "555", "Hello!", "--token", TOKEN, "-f", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["message_id"] == 7
    assert data["text"] == "Hello!"


@respx.mock
def test_updates_filter_by_chat():
    respx.get(_url("getUpdates")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "message_id": 1,
                            "date": 1,
                            "chat": {"id": 100, "type": "private", "first_name": "A"},
                            "from": {"id": 100, "is_bot": False, "first_name": "A"},
                            "text": "from 100",
                        },
                    },
                    {
                        "update_id": 2,
                        "message": {
                            "message_id": 2,
                            "date": 2,
                            "chat": {"id": 200, "type": "private", "first_name": "B"},
                            "from": {"id": 200, "is_bot": False, "first_name": "B"},
                            "text": "from 200",
                        },
                    },
                ],
            },
        )
    )
    result = runner.invoke(
        app,
        ["updates", "--chat-id", "200", "--token", TOKEN, "-f", "json"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["chat"]["id"] == 200


@respx.mock
def test_updates_empty_human():
    respx.get(_url("getUpdates")).mock(
        return_value=httpx.Response(200, json={"ok": True, "result": []})
    )
    result = runner.invoke(app, ["updates", "--token", TOKEN])
    assert result.exit_code == 0
    assert "No messages" in result.output


@respx.mock
def test_chat_info_json():
    respx.get(_url("getChat")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {"id": 9, "type": "group", "title": "My Group"},
            },
        )
    )
    result = runner.invoke(
        app, ["chat", "9", "--token", TOKEN, "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == 9
    assert data["title"] == "My Group"


@respx.mock
def test_token_from_env_var(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", TOKEN)
    respx.get(_url("getMe")).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {"id": 1, "is_bot": True, "first_name": "X"},
            },
        )
    )
    result = runner.invoke(app, ["me"])
    assert result.exit_code == 0


@respx.mock
def test_me_error_human_exits_nonzero():
    respx.get(_url("getMe")).mock(
        return_value=httpx.Response(
            200, json={"ok": False, "description": "chat not found"}
        )
    )
    result = runner.invoke(app, ["me", "--token", TOKEN])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_no_args_shows_help():
    result = runner.invoke(app, [])
    assert result.exit_code != 0
    assert "Usage" in result.output
