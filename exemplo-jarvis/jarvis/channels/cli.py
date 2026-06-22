"""In-memory / CLI channel for tests and the smoke script.

Implements BaseChannel without any network. You push IncomingMessages in and it
calls on_message; outgoing messages are captured in `.outbox`.
"""
import time

from .base import BaseChannel, IncomingMessage, OutgoingMessage


class CLIChannel(BaseChannel):
    def __init__(self, chat_id: str = "cli", sender_name: str = "Nei"):
        self.chat_id = chat_id
        self.sender_name = sender_name
        self._on_message = None
        self.outbox: list[OutgoingMessage] = []

    async def start(self, on_message) -> None:
        self._on_message = on_message

    async def send(self, message: OutgoingMessage) -> None:
        self.outbox.append(message)

    async def stop(self) -> None:
        self._on_message = None

    # --- test/smoke helper: simulate a user typing a line ---
    async def feed(self, text: str) -> str:
        """Deliver a user message through the wired handler; return reply text."""
        if self._on_message is None:
            raise RuntimeError("channel not started")
        incoming = IncomingMessage(
            text=text,
            sender_id="1",
            sender_name=self.sender_name,
            chat_id=self.chat_id,
            timestamp=time.time(),
        )
        reply = await self._on_message(incoming)
        await self.send(OutgoingMessage(text=reply, chat_id=self.chat_id))
        return reply
