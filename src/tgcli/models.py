"""Data models for Telegram entities used by the CLI."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class User:
    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None

    @property
    def display_name(self) -> str:
        name = self.first_name
        if self.last_name:
            name = f"{name} {self.last_name}"
        return name

    @property
    def mention(self) -> str:
        return f"@{self.username}" if self.username else self.display_name

    @classmethod
    def from_api(cls, data: dict) -> User:
        return cls(
            id=data["id"],
            is_bot=data.get("is_bot", False),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name"),
            username=data.get("username"),
        )


@dataclass(frozen=True, slots=True)
class Chat:
    id: int
    type: str
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @property
    def display_name(self) -> str:
        if self.title:
            return self.title
        name = self.first_name or ""
        if self.last_name:
            name = f"{name} {self.last_name}".strip()
        if name:
            return name
        if self.username:
            return f"@{self.username}"
        return f"Chat {self.id}"

    @classmethod
    def from_api(cls, data: dict) -> Chat:
        return cls(
            id=data["id"],
            type=data.get("type", "unknown"),
            title=data.get("title"),
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
        )


@dataclass(frozen=True, slots=True)
class Message:
    message_id: int
    date: int
    chat: Chat
    sender: User | None
    text: str | None = None
    caption: str | None = None

    @property
    def body(self) -> str:
        return self.text or self.caption or ""

    @classmethod
    def from_api(cls, data: dict) -> Message:
        chat = Chat.from_api(data["chat"])
        sender = (
            User.from_api(data["from"])
            if "from" in data
            else None
        )
        return cls(
            message_id=data["message_id"],
            date=data["date"],
            chat=chat,
            sender=sender,
            text=data.get("text"),
            caption=data.get("caption"),
        )


@dataclass(slots=True)
class Update:
    update_id: int
    message: Message | None = None

    @classmethod
    def from_api(cls, data: dict) -> Update:
        message = (
            Message.from_api(data["message"])
            if "message" in data
            else None
        )
        return cls(update_id=data["update_id"], message=message)


@dataclass(slots=True)
class BotInfo:
    user: User
    can_join_groups: bool = False
    can_read_all_group_messages: bool = False
    supports_inline_queries: bool = False
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_api(cls, data: dict) -> BotInfo:
        return cls(
            user=User.from_api(data),
            can_join_groups=data.get("can_join_groups", False),
            can_read_all_group_messages=data.get(
                "can_read_all_group_messages", False
            ),
            supports_inline_queries=data.get(
                "supports_inline_queries", False
            ),
            raw=data,
        )
