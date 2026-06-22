"""Telegram channel — STRUCTURAL ONLY (Task 4.2).

Implements BaseChannel and the message-splitting logic, but does NOT import or
require python-telegram-bot and is never .start()-ed in tests (no token, no
network). The real implementation would long-poll via python-telegram-bot v21+.
The 4096-char split helper is real and unit-testable.
"""
from .base import BaseChannel, OutgoingMessage

TELEGRAM_MAX = 4096


def split_message(text: str, limit: int = TELEGRAM_MAX) -> list[str]:
    """Split long text at paragraph boundaries, then hard-wrap if still too long."""
    if len(text) <= limit:
        return [text]
    chunks, buf = [], ""
    for para in text.split("\n\n"):
        candidate = (buf + "\n\n" + para) if buf else para
        if len(candidate) <= limit:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
            buf = ""
        while len(para) > limit:
            chunks.append(para[:limit])
            para = para[limit:]
        buf = para
    if buf:
        chunks.append(buf)
    return chunks


class TelegramChannel(BaseChannel):
    def __init__(self, config=None, token: str | None = None):
        self.config = config
        self.token = token  # would come from the secret store in production
        self._running = False
        self.sent: list[OutgoingMessage] = []  # captured for inspection/tests

    async def start(self, on_message) -> None:
        # Real impl: build Application(token).run_polling(); wire handlers ->
        # IncomingMessage -> on_message. Guarded so it can never run token-less.
        if not self.token:
            raise RuntimeError(
                "TelegramChannel.start requires a bot token (set up via wizard). "
                "Not runnable offline — structural only."
            )
        self._running = True  # pragma: no cover

    async def send(self, message: OutgoingMessage) -> None:
        # Real impl: bot.send_message(chat_id, chunk, parse_mode='Markdown')
        # per split chunk. Here we just record the chunks.
        for chunk in split_message(message.text):
            self.sent.append(OutgoingMessage(text=chunk, chat_id=message.chat_id))

    async def stop(self) -> None:
        self._running = False
