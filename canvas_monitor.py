import asyncio
import os
import pickle
import threading
import tkinter
from queue import Queue
from typing import Counter, List

import aiohttp
from loguru import logger

WS_ADDRESS = "wss://ws.luogu.com.cn/ws"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
)


def to_hex(r: int, g: int, b: int) -> str:
    return f"#{hex(r)[2:].zfill(2)}{hex(g)[2:].zfill(2)}{hex(b)[2:].zfill(2)}"


def visualize(time: int) -> str:
    time *= 200
    r = time % 256
    g = (time // 256) % 256
    b = (time // 256 // 256) % 256
    return to_hex(r, g, b)


WIDTH = 1000
HEIGHT = 600


async def update():
    async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}).ws_connect(
        WS_ADDRESS
    ) as ws_session:

        data: Counter[(int, int)] = Counter()

        if os.path.exists("./history.pickle"):
            with open("./history.pickle", "rb") as f:
                data = pickle.load(f)

        await ws_session.send_json(
            {"type": "join_channel", "channel": "paintboard", "channel_param": ""}
        )

        logger.info("Websocket online.")

        while True:

            json_data = await ws_session.receive_json()
            if json_data["type"] == "paintboard_update":
                x, y, c = json_data["x"], json_data["y"], json_data["color"]

                data[(x, y)] += 1

                logger.debug(f"Paint: ({x}, {y}): {visualize(c)}")
                with open("./history.pickle", "wb") as f:
                    pickle.dump(data, f)


if __name__ == "__main__":
    asyncio.run(update())
