# tgcli

A minimal command-line tool for interacting with Telegram via a **bot token**.
List chats that have messaged your bot, read recent messages, and send new
ones — all from your terminal.

Every command prints friendly, human-readable output by default and supports
`--format json` for scripting.

## Installation

```bash
# from PyPI
pip install tgcli

# or with uv
uv tool install tgcli

# straight from source
uv tool install git+https://github.com/MatthewScholefield/tgcli
```

## Authentication

Grab a token from [@BotFather](https://t.me/BotFather) and either pass it on
every command with `-t`/`--token`, or export it once:

```bash
export TELEGRAM_BOT_TOKEN=123456:ABC-DEF
```

## Commands

### `tgcli me`

Verify the token and show the bot's identity.

```bash
tgcli me
```

### `tgcli chats`

List chats that have recently messaged the bot (the easiest way to discover
chat ids). Send a message to your bot first, then run:

```bash
tgcli chats
tgcli chats --format json
```

### `tgcli send`

Send a text message to a chat.

```bash
tgcli send 555 "Hello there!"
tgcli send @channelusername "Announcement" --parse-mode HTML
tgcli send 555 "replying!" --reply-to 42 --silent
```

### `tgcli updates`

Show recent messages the bot has received, optionally filtered to one chat.

```bash
tgcli updates
tgcli updates --chat-id 555 --limit 50
tgcli updates -c 555 -f json
```

### `tgcli chat`

Show information about a specific chat.

```bash
tgcli chat 555
tgcli chat @channelusername
```

## Global options

| Option             | Description                                      |
| ------------------ | ------------------------------------------------ |
| `-t`, `--token`    | Bot token (or set `$TELEGRAM_BOT_TOKEN`)         |
| `-f`, `--format`   | Output format: `human` (default) or `json`       |

## Development

Built with [uv](https://docs.astral.sh/uv/) and the `uv_build` backend.

```bash
uv sync          # install dev dependencies
uv run pytest    # run the test suite
uv build         # build sdist + wheel
```

## License

[MIT](LICENSE)
