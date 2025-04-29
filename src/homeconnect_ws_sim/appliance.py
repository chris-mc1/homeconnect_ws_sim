from __future__ import annotations

import logging
import ssl
from base64 import urlsafe_b64decode
from typing import TYPE_CHECKING

from aiohttp import web

from src.homeconnect_ws_sim.const import DEFAULT_INFO, DEFAULT_SERVICE_VERSIONS

from .entities import (
    ActiveProgram,
    Command,
    Entity,
    Event,
    Option,
    Program,
    SelectedProgram,
    Setting,
    Status,
)
from .session import SimSession

if TYPE_CHECKING:
    import asyncio

    from homeconnect_websocket import DeviceDescription
    from homeconnect_websocket.entities import DeviceInfo
    from homeconnect_websocket.message import Message


class SimAppliance:
    """Base HomeConnect Appliance."""

    info: DeviceInfo
    entities_uid: dict[int, Entity]
    "entities by uid"

    entities: dict[str, Entity]
    "entities by name"

    status: dict[str, Status]
    "status entities by name"

    settings: dict[str, Setting]
    "setting entities by name"

    events: dict[str, Event]
    "event entities by name"

    commands: dict[str, Command]
    "command entities by name"

    options: dict[str, Option]
    "option entities by name"

    programs: dict[str, Program]
    "program entities by name"
    sessions: set[SimSession]
    service_versions: dict[str, int]
    _tls_site: web.TCPSite
    _runner: web.AppRunner

    def __init__(
        self,
        description: DeviceDescription,
        psk64: str,
        services: dict[str, int] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        HomeConnect Appliance.

        Args:
        ----
            description (DeviceDescription): parsed Device description
            host (str): Host
            logger (Optional[Logger]): Logger

        """
        self.psk64 = psk64
        self.service_versions = services if services else DEFAULT_SERVICE_VERSIONS
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger.getChild("appliance")

        self.info = DEFAULT_INFO.copy()
        if "info":
            self.info.update(description["info"])

        self.entities_uid = {}
        self.entities = {}
        self.status = {}
        self.settings = {}
        self.events = {}
        self.commands = {}
        self.options = {}
        self.programs = {}
        self.sessions = set()
        self._create_entities(description)

    def _create_entities(self, description: DeviceDescription) -> None:
        """Create Entities from Device description."""
        for status in description["status"]:
            entity = Status(status, self)
            self.status[entity.name] = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

        for setting in description["setting"]:
            entity = Setting(setting, self)
            self.settings[entity.name] = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

        for event in description["event"]:
            entity = Event(event, self)
            self.events[entity.name] = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

        for command in description["command"]:
            entity = Command(command, self)
            self.commands[entity.name] = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

        for option in description["option"]:
            entity = Option(option, self)
            self.options[entity.name] = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

        for program in description["program"]:
            entity = Program(program, self)
            self.programs[entity.name] = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

        if "activeProgram" in description:
            entity = ActiveProgram(description["activeProgram"], self)
            self._active_program = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

        if "selectedProgram" in description:
            entity = SelectedProgram(description["selectedProgram"], self)
            self._selected_program = entity
            self.entities[entity.name] = entity
            self.entities_uid[entity.uid] = entity

    async def _websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        self._logger.info("WebSocket connection from %s", request.remote)
        websocket = web.WebSocketResponse(heartbeat=2)
        await websocket.prepare(request)
        sessions = SimSession(websocket, self)
        self.sessions.add(sessions)
        await sessions.run()
        self.sessions.remove(sessions)
        return websocket

    async def start(self, loop: asyncio.AbstractEventLoop) -> None:
        app = web.Application(loop=loop)
        app.router.add_get("/homeconnect", self._websocket_handler)
        self._runner = web.AppRunner(app)
        await self._runner.setup()

        psk = urlsafe_b64decode(self.psk64 + "===")
        psk.hex()
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.set_ciphers("ALL")
        ssl_context.check_hostname = False
        ssl_context.set_psk_server_callback(lambda _: psk)
        self._tls_site = web.TCPSite(self._runner, port=443, ssl_context=ssl_context)

        await self._tls_site.start()

    async def stop(self) -> None:
        await self._runner.cleanup()

    def get_all_description_changes(self) -> list[dict]:
        values = []
        for entity in self.entities.values():
            changes = entity.get_description_changes()
            if len(changes) > 1:
                values.append(changes)
        return values

    def get_all_values(self) -> list[dict]:
        return [
            {"uid": entity.uid, "value": entity.value_raw}
            for entity in self.entities_uid.values()
            if entity.value_raw is not None
        ]

    def dump(self) -> dict:
        """Dump Appliance state."""
        return {
            "entities": [entity.dump() for entity in self.entities.values()],
            "service_versions": self.service_versions,
        }

    async def set_state(self, state: list[dict]) -> None:
        for entity in state:
            await self.entities_uid[entity["uid"]].set_state(entity)

    async def update_entities(self, data: list[dict]) -> None:
        """Update entities from Message data."""
        for entity in data:
            uid = int(entity["uid"])
            if uid in self.entities_uid:
                await self.entities_uid[uid].update(entity)
            else:
                self._logger.debug("Recived Update for unkown entity %s", uid)

    async def send(self, message: Message) -> None:
        for session in self.sessions:
            await session.send(message)
