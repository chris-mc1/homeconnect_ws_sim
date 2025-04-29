from __future__ import annotations

import json
import logging
import re
from importlib.resources import files
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile

from aiohttp import BodyPartReader, MultipartReader, web
from homeconnect_websocket import parse_device_description

from .appliance import SimAppliance

if TYPE_CHECKING:
    import asyncio

    from homeconnect_websocket import DeviceDescription

    from .entities import Entity

_LOGGER = logging.getLogger(__name__)


async def process_zip_file(
    field: MultipartReader | BodyPartReader,
) -> dict[str, dict | DeviceDescription]:
    temp_file = b""
    while True:
        chunk = await field.read_chunk()  # 8192 bytes by default.
        if not chunk:
            break
        temp_file = temp_file + chunk
    with ZipFile(file=BytesIO(temp_file)) as profile_file:
        re_info = re.compile(".*.json$")
        infolist = profile_file.infolist()
        for file in infolist:
            if re_info.match(file.filename):
                appliance_info = json.load(profile_file.open(file))

                description_file_name = appliance_info["deviceDescriptionFileName"]
                feature_file_name = appliance_info["featureMappingFileName"]
                description_file = profile_file.open(description_file_name).read()
                feature_file = profile_file.open(feature_file_name).read()

                appliance_description = parse_device_description(description_file, feature_file)
                return {
                    "description": appliance_description,
                    "psk64": appliance_info["key"],
                }
        return None


async def process_json_file(
    field: MultipartReader | BodyPartReader,
) -> DeviceDescription:
    file = await field.read()
    data = json.loads(file.decode())
    return {"psk64": data["key"]}


async def process_config_entry_file(
    field: MultipartReader | BodyPartReader,
) -> dict[str, dict | DeviceDescription]:
    file = await field.read()
    data = json.loads(file.decode())["data"]

    config = {
        "state": data["appliance_state"]["entities"],
        "services": data["appliance_state"]["service_versions"],
        "description": data["entry_data"]["description"],
        "psk64": data["entry_data"]["psk"],
    }
    if data["entry_data"]["psk"] != "**REDACTED**":
        config["psk64"] = data["entry_data"]["psk"]
    return config


class Server:
    appliance: SimAppliance = None

    def __init__(
        self, config_file: Path, loop: asyncio.AbstractEventLoop, psk64: str | None = None
    ):
        self.loop = loop
        self.psk64 = psk64
        self.config_file = config_file
        self.websockets: list[web.WebSocketResponse] = []
        app = web.Application(loop=loop)
        app.add_routes(
            [
                web.static(
                    "/assets",
                    Path(files()) / "frontend/dist/assets",
                ),
                web.get("/{tail:.*}", self.root_handler),
                web.post("/api/file_upload", self.file_upload_handler),
                web.get("/api/ws", self.websocket_handler),
            ]
        )
        self.runner = web.AppRunner(app, access_log=None)

    async def run(self, port: int) -> None:
        await self.runner.setup()
        self.main_site = web.TCPSite(self.runner, port=port)
        await self.main_site.start()
        if self.config_file and self.config_file.exists():
            with self.config_file.open() as file:
                appliance_config = json.load(file)
            await self._start_appliance(
                description=appliance_config["description"],
                psk64=appliance_config["psk64"],
                services=appliance_config.get("services"),
                state=appliance_config.get("state"),
            )

    async def root_handler(self, _: web.Request) -> web.Response:
        return web.FileResponse(Path(files()) / "frontend/dist/index.html")

    async def file_upload_handler(self, request: web.Request) -> web.Response:
        _LOGGER.info("Got file upload")
        reader = await request.multipart()
        xml_feature_file = None
        xml_description_file = None
        appliance_config = {}
        async for field in reader:
            if field.filename.endswith(".zip"):
                appliance_config.update(await process_zip_file(field))
            elif field.filename.endswith(".json"):
                if field.filename.startswith("config_entry"):
                    appliance_config.update(await process_config_entry_file(field))
                else:
                    appliance_config.update(await process_json_file(field))
            elif field.filename.endswith("DeviceDescription.xml"):
                xml_description_file = await field.read()
            elif field.filename.endswith("FeatureMapping.xml"):
                xml_feature_file = await field.read()

        if xml_description_file and xml_feature_file:
            appliance_config.update(
                {"description": parse_device_description(xml_description_file, xml_feature_file)}
            )
        if self.psk64:
            appliance_config["psk64"] = self.psk64
        if "description" not in appliance_config:
            _LOGGER.error("No Description")
            return web.Response()
        if "psk64" not in appliance_config:
            _LOGGER.error("No Key")
            return web.Response()

        _LOGGER.info("Got description, starting appliance")
        if self.appliance:
            await self.appliance.stop()
        if self.config_file:
            with self.config_file.open("w") as file:
                json.dump(appliance_config, file)
        await self._start_appliance(
            description=appliance_config["description"],
            psk64=appliance_config["psk64"],
            services=appliance_config.get("services"),
            state=appliance_config.get("state"),
        )
        await self.async_websocket_broadcast(
            {
                "action": "init",
                "entities": self.appliance.dump()["entities"],
            }
        )
        return web.Response()

    async def _start_appliance(
        self,
        description: dict,
        psk64: str,
        state: dict | None = None,
        services: dict | None = None,
    ) -> None:
        self.appliance = SimAppliance(
            description=description,
            psk64=psk64,
            services=services,
        )
        if state:
            await self.appliance.set_state(state)
        for entity in self.appliance.entities.values():
            entity.register_callback(self._entity_update)
        await self.appliance.start(loop=self.loop)
        _LOGGER.info("Appliance started")

    async def _entity_update(self, entity: Entity) -> None:
        await self.async_websocket_broadcast(
            {
                "action": "update",
                "entity": entity.dump(),
            }
        )

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        _LOGGER.info("WebSocket connection from %s", request.remote)
        ws = web.WebSocketResponse(heartbeat=2)
        await ws.prepare(request)
        if self.appliance:
            await ws.send_json(
                {
                    "action": "init",
                    "entities": self.appliance.dump()["entities"],
                }
            )
        self.websockets.append(ws)
        while not ws.closed:
            async for msg in ws:
                if msg.type != web.WSMsgType.TEXT:
                    continue
                message = msg.json()
                if message["action"] == "set":
                    _LOGGER.info("Set state: %s", message)
                    entity = self.appliance.entities_uid[message["uid"]]
                    await entity.set_state({message["key"]: message["value"]})
                    await self.async_websocket_broadcast(
                        {
                            "action": "update",
                            "entity": entity.dump(),
                        }
                    )

        self.websockets.remove(ws)
        _LOGGER.debug("WebSocket connection from %s closed", request.remote)
        return ws

    async def async_websocket_broadcast(self, data: dict | None = None) -> None:
        for websocket in self.websockets:
            try:
                await websocket.send_json(data)
            except (RuntimeError, ConnectionResetError):
                await websocket.close()
                self.websockets.remove(websocket)
            except Exception:
                _LOGGER.exception("Error sending WebSocket broadcast")
