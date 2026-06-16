"""Output rendering: human-readable tables by default, JSON on demand."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import Any, Sequence

from rich.console import Console
from rich.table import Table

from .client import timestamp
from .models import BotInfo, Chat, Message


def _model_dict(obj: Any) -> Any:
    """Recursively convert dataclass instances to plain JSON data."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _model_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_model_dict(i) for i in obj]
    return obj


class Renderer:
    """Render structured results either as formatted text or JSON."""

    def __init__(self, fmt: str = "human") -> None:
        self.fmt = fmt
        self.console = Console()
        self.err = Console(stderr=True)

    # -- helpers ---------------------------------------------------------

    def _table(self, title: str, columns: Sequence[str]) -> Table:
        table = Table(title=title, show_lines=False)
        for col in columns:
            table.add_column(col)
        return table

    def _emit_json(self, data: Any) -> None:
        json.dump(_model_dict(data), sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")

    # -- error -----------------------------------------------------------

    def error(self, message: str) -> None:
        if self.fmt == "json":
            json.dump({"error": message}, sys.stdout, indent=2)
            sys.stdout.write("\n")
        else:
            self.err.print(f"[bold red]Error:[/] {message}")

    # -- views -----------------------------------------------------------

    def bot(self, info: BotInfo) -> None:
        if self.fmt == "json":
            return self._emit_json(info)
        u = info.user
        self.console.print(
            f"[bold green]✓[/] Connected as [cyan]{u.display_name}[/]"
            f" ([dim]id={u.id}[/])"
        )
        flags = []
        if info.can_join_groups:
            flags.append("can-join-groups")
        if info.can_read_all_group_messages:
            flags.append("reads-all-group-messages")
        if info.supports_inline_queries:
            flags.append("inline-queries")
        if flags:
            self.console.print(f"[dim]Capabilities:[/] {', '.join(flags)}")

    def chats(self, chats: Sequence[Chat]) -> None:
        if self.fmt == "json":
            return self._emit_json(list(chats))
        if not chats:
            self.console.print("[dim]No chats found.[/]")
            self.console.print(
                "[dim]Send a message to your bot first, then run "
                "'flaregram chats' again.[/]"
            )
            return
        table = self._table(
            "Recent chats", ["Chat ID", "Type", "Name"]
        )
        for c in chats:
            table.add_row(str(c.id), c.type, c.display_name)
        self.console.print(table)

    def messages(self, messages: Sequence[Message]) -> None:
        if self.fmt == "json":
            return self._emit_json(list(messages))
        if not messages:
            self.console.print("[dim]No messages to show.[/]")
            return
        for m in messages:
            sender = m.sender.mention if m.sender else "unknown"
            when = timestamp(m.date)
            self.console.print(
                f"[bold]{sender}[/] [dim]{when} (id={m.message_id})[/]"
            )
            if m.body:
                self.console.print(f"  {m.body}")

    def sent(self, msg: Message) -> None:
        if self.fmt == "json":
            return self._emit_json(msg)
        self.console.print(
            f"[green]✓[/] Sent to [cyan]{msg.chat.display_name}[/] "
            f"([dim]id={msg.chat.id}, msg={msg.message_id}[/])"
        )

    def chat(self, chat: Chat) -> None:
        if self.fmt == "json":
            return self._emit_json(chat)
        self.console.print(
            f"[cyan]{chat.display_name}[/] "
            f"([dim]id={chat.id}, type={chat.type}[/])"
        )
