from __future__ import annotations

import asyncio
import logging
from argparse import ArgumentParser
from pathlib import Path

from .server import Server

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
)
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-f", type=Path, default=None, dest="config_file")
    parser.add_argument("-p", type=int, default=8080, dest="port")
    parser.add_argument("-psk", type=str, default=None, dest="psk64")
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    server = Server(args.config_file, loop, psk64=args.psk64)
    loop.run_until_complete(server.run(args.port))
    loop.run_forever()
