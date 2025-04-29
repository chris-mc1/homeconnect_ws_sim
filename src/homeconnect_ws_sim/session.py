from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

from homeconnect_websocket.message import Action, Message, load_message

from homeconnect_ws_sim.const import NI_CONFIG, NI_INFO

from .hc_socket import SimSocket

if TYPE_CHECKING:
    from aiohttp import web

    from .appliance import SimAppliance


class SimSession:
    _sid: int | None = None
    _last_msg_id: int | None = None

    def __init__(
        self,
        websocket: web.WebSocketResponse,
        appliance: SimAppliance,
        *,
        logger: logging.Logger | None = None,
    ):
        self._appliance = appliance
        self.app_info = {
            "endDeviceID": 0,
            "connected": True,
            "protected": False,
        }
        self._socket = SimSocket(
            host=websocket.get_extra_info("peername")[0],
            websocket=websocket,
            logger=logger,
        )

        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger.getChild("session")

    async def run(self) -> None:
        self._sid = random.randrange(1000000000, 9999999999)  # noqa: S311
        self._last_msg_id = random.randrange(1000000000, 9999999999)  # noqa: S311
        msg = Message(
            resource="/ei/initialValues",
            action=Action.POST,
            data=[{"edMsgID": random.randrange(1000000000, 9999999999)}],  # noqa: S311
        )
        await self.send(msg)
        try:
            async for message in self._socket:
                # recv messages
                message_obj = load_message(message)
                await self._message_handler(message_obj)

        except Exception:
            self._logger.exception("Receive loop Exception")
        self._logger.info("Closed")

    async def _message_handler(self, message: Message) -> None:
        if message.action == Action.GET:
            if message.resource == "/ci/services":
                resp = message.responde(
                    data=[
                        {"service": service, "version": version}
                        for service, version in self._appliance.service_versions.items()
                    ]
                )
                await self.send(resp)
            elif message.resource == "/iz/info":
                resp = message.responde(data=self._appliance.info)
                await self.send(resp)
            elif message.resource == "/ci/registeredDevices":
                resp = message.responde(data=[self.app_info])
                await self.send(resp)
            elif message.resource == "/ci/pairableDevices":
                resp = message.responde(data=[{"deviceTypeList": []}])
                await self.send(resp)
            elif message.resource == "/ni/info":
                resp = message.responde(data=[NI_INFO])
                await self.send(resp)
            elif message.resource == "/ni/config":
                resp = message.responde(data=[NI_CONFIG])
                await self.send(resp)
            elif message.resource == "/ro/allDescriptionChanges":
                resp = message.responde(data=self._appliance.get_all_description_changes())
                await self.send(resp)
            elif message.resource == "/ro/allMandatoryValues":
                resp = message.responde(data=self._appliance.get_all_values())
                await self.send(resp)
            else:
                resp = message.responde()
                resp.code = 404
                await self.send(resp)
        elif message.action == Action.RESPONSE:
            if message.resource == "/ei/initialValues":
                self.app_info.update(message.data[0])
            else:
                resp = message.responde()
                resp.code = 404
                await self.send(resp)
        elif message.action == Action.POST:
            if message.resource == "/ro/values":
                await self._appliance.update_entities(message.data)
                resp = message.responde()
                await self.send(resp)
            elif message.resource in {"/ro/activeProgram", "/ro/selectedProgram"}:
                resp = message.responde()
                await self.send(resp)
        elif message.action == Action.NOTIFY:
            if message.resource == "/ei/deviceReady":
                pass
            else:
                resp = message.responde()
                resp.code = 404
                await self.send(resp)
        else:
            resp = message.responde()
            resp.code = 404
            await self.send(resp)

    def _set_message_info(self, message: Message) -> None:
        """Set Message infos. called before sending message."""
        # Set service version
        if message.version is None:
            service = message.resource[1:3]
            message.version = self._appliance.service_versions.get(service, 1)

        # Set sID
        if message.sid is None:
            message.sid = self._sid

        # Set msgID
        if message.msg_id is None:
            message.msg_id = self._last_msg_id
            self._last_msg_id += 1

    async def send(self, message: Message) -> None:
        self._set_message_info(message)
        await self._socket.send(message.dump())
