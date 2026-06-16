"""Command line interface for the Telegram bot CLI."""

from __future__ import annotations

import os
from typing import Optional

import typer

from .client import TelegramClient, TelegramError
from .models import Chat
from .output import Renderer

app = typer.Typer(
    name="tgtool",
    help=(
        "A minimal Telegram bot CLI. Authenticate with a bot token to "
        "list chats, read recent messages, and send new ones."
    ),
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
FormatOption = typer.Option(
    "human",
    "--format",
    "-f",
    help="Output format: human-readable table or JSON.",
    case_sensitive=False,
)
TokenOption = typer.Option(
    None,
    "--token",
    "-t",
    envvar=TOKEN_ENV,
    help=(
        "Telegram bot token from @BotFather. "
        f"Can also be set via ${TOKEN_ENV}."
    ),
)


def _make_client(token: Optional[str]) -> TelegramClient:
    return TelegramClient(token or "")


def _run(
    token: Optional[str],
    fmt: str,
    fn,
) -> None:
    """Execute a client action and render the result or an error."""
    render = Renderer(fmt)
    try:
        fn(_make_client(token), render)
    except TelegramError as exc:
        render.error(str(exc))
        raise typer.Exit(code=1)


@app.command()
def me(
    token: Optional[str] = TokenOption,
    fmt: str = FormatOption,
) -> None:
    """Verify the bot token and show bot information."""

    def action(client: TelegramClient, render: Renderer) -> None:
        render.bot(client.get_me())

    _run(token, fmt, action)


@app.command(name="chats")
def list_chats(
    token: Optional[str] = TokenOption,
    fmt: str = FormatOption,
) -> None:
    """List chats that have recently messaged the bot."""

    def action(client: TelegramClient, render: Renderer) -> None:
        updates = client.get_updates(limit=100)
        chats: dict[int, Chat] = {}
        for upd in updates:
            if upd.message:
                chats[upd.message.chat.id] = upd.message.chat
        render.chats(list(chats.values()))

    _run(token, fmt, action)


@app.command(name="send")
def send_message(
    chat_id: str = typer.Argument(
        ..., help="Target chat id (numeric or @channelusername)."
    ),
    text: str = typer.Argument(..., help="Message text to send."),
    reply_to: Optional[int] = typer.Option(
        None, "--reply-to", help="Message id to reply to."
    ),
    parse_mode: Optional[str] = typer.Option(
        None,
        "--parse-mode",
        help="Formatting: MarkdownV2, HTML, or Markdown (legacy).",
    ),
    silent: bool = typer.Option(
        False, "--silent", help="Send without notification sound."
    ),
    token: Optional[str] = TokenOption,
    fmt: str = FormatOption,
) -> None:
    """Send a text message to a chat."""

    def action(client: TelegramClient, render: Renderer) -> None:
        msg = client.send_message(
            chat_id,
            text,
            reply_to=reply_to,
            parse_mode=parse_mode,
            disable_notification=silent,
        )
        render.sent(msg)

    _run(token, fmt, action)


@app.command(name="updates")
def list_updates(
    chat_id: Optional[str] = typer.Option(
        None, "--chat-id", "-c", help="Only show updates from this chat."
    ),
    limit: int = typer.Option(
        20, "--limit", "-n", help="Maximum number of updates to show."
    ),
    token: Optional[str] = TokenOption,
    fmt: str = FormatOption,
) -> None:
    """Show recent messages the bot has received."""

    def action(client: TelegramClient, render: Renderer) -> None:
        updates = client.get_updates(limit=min(max(limit, 1), 100))
        messages = [
            u.message for u in updates if u.message is not None
        ]
        if chat_id is not None:
            messages = [
                m
                for m in messages
                if str(m.chat.id) == str(chat_id)
                or m.chat.username == str(chat_id).lstrip("@")
            ]
        render.messages(messages)

    _run(token, fmt, action)


@app.command(name="chat")
def chat_info(
    chat_id: str = typer.Argument(
        ..., help="Chat id (numeric or @channelusername)."
    ),
    token: Optional[str] = TokenOption,
    fmt: str = FormatOption,
) -> None:
    """Show information about a specific chat."""

    def action(client: TelegramClient, render: Renderer) -> None:
        render.chat(client.get_chat(chat_id))

    _run(token, fmt, action)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
