from __future__ import annotations

import logging

import aiohttp
from aiohttp import web


class SimSocket:
    def __init__(
        self, host: str, websocket: web.WebSocketResponse, logger: logging.Logger | None = None
    ):
        self._websocket = websocket
        self._host = host

        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger.getChild("socket")

    async def send(self, message: str) -> None:
        """Send message."""
        self._logger.debug("Send     %s: %s", self._host, message)
        await self._websocket.send_str(message)

    async def _receive(self, message: aiohttp.WSMessage) -> str:
        self._logger.debug("Received %s: %s", self._host, str(message.data))
        if message.type == aiohttp.WSMsgType.ERROR:
            raise message.data
        return str(message.data)

    @property
    def closed(self) -> bool:
        """True if underlying websocket is closed."""
        if self._websocket:
            return self._websocket.closed
        return True

    def __aiter__(self) -> SimSocket:
        return self

    async def __anext__(self) -> str:
        msg = await self._websocket.__anext__()
        return await self._receive(msg)
