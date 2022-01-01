import argparse
import asyncio
import json
import pickle
from typing import Counter, Dict, List, Literal, Tuple

import aiohttp
import aiohttp.client_ws
from loguru import logger

LUOGU = "https://www.luogu.com.cn"
LUOGU_WS = "wss://ws.luogu.com.cn"

WS_ADDRESS = f"{LUOGU_WS}/ws"
POST_ADDRESS = f"{LUOGU}/paintboard/paint?token={{token}}"
GET_ADDRESS = f"{LUOGU}/paintboard/board"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
)

INTERVAL = 0.2


async def write(
    token: str,
    session: aiohttp.ClientSession,
    error: Dict[Tuple[int, int], int],
    history: Counter[Tuple[int, int]],
):
    await asyncio.sleep(10)
    ADDR = POST_ADDRESS.format(token=token)
    while True:
        if error:
            (x, y), c = error.popitem()
            resp = await session.post(
                ADDR, data={"x": x, "y": y, "color": data[(x, y)]}
            )
            logger.info(
                f"Posted to {(x, y)} with color {data[(x, y)]}. Code: {resp.status}"
            )
            if resp.status == 200:
                await asyncio.sleep(INTERVAL)
        else:
            await asyncio.sleep(0)


async def update(
    session: aiohttp.ClientSession,
    current: Dict[Tuple[int, int], int],
    error: Dict[Tuple[int, int], int],
    data: Dict[Tuple[int, int], int],
):
    while True:
        logger.info("Fetching data...")
        init_data = await session.get(GET_ADDRESS)
        for x, line in enumerate((await init_data.text()).split("\n")):
            for y, char in enumerate(line):
                current[(x, y)] = int(char, base=32)

        for k, v in data.items():
            if current[k] != v:
                error[k] = v
            else:
                if k in error:
                    del error[k]
        logger.warning(
            f"\nError: {len(error)} points\nCorrect: {len(data) - len(error)} points\nPercentage: {(len(data) - len(error)) / len(data) :.2%}"
        )

        logger.info("Scheduled update in 10s.")

        await asyncio.sleep(10.0)


async def ws_update(
    session: aiohttp.ClientSession,
    current: Dict[Tuple[int, int], int],
    error: Dict[Tuple[int, int], int],
    data: Dict[Tuple[int, int], int],
):
    while True:
        try:
            async with session.ws_connect(WS_ADDRESS) as ws_session:
                logger.info("Websocket online.")

                await ws_session.send_json(
                    {
                        "type": "join_channel",
                        "channel": "paintboard",
                        "channel_param": "",
                    }
                )

                while True:
                    json_data = await ws_session.receive_json()
                    if json_data["type"] == "paintboard_update":
                        x, y, c = json_data["x"], json_data["y"], json_data["color"]
                        current[(x, y)] = c
                        if (x, y) in data:
                            if c != data[(x, y)]:
                                error[(x, y)] = c
                            else:
                                if (x, y) in error:
                                    del error[(x, y)]
        except Exception:
            pass


async def main(data: Dict[Tuple[int, int], int], tokens: List[str]):

    async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        current: Dict[Tuple[int, int], int] = {}
        history: Counter[Tuple[int, int]] = Counter()
        error: Dict[Tuple[int, int], int] = {}

        logger.info("Initializing connection...")

        asyncio.create_task(update(session, current, error, data))

        asyncio.create_task(ws_update(session, current, error, data))

        write_tasks = []

        for token in tokens:
            write_tasks.append(
                asyncio.create_task(write(token, session, error, history))
            )

        await asyncio.gather(*write_tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type",
        "-t",
        choices=["json", "pickle"],
        default="pickle",
        help="File format.",
    )
    parser.add_argument(
        "--file", "-f", default="./output.pickle", help="File location."
    )
    parser.add_argument("--token-file", "--token", default="./token.json")

    nbsp = parser.parse_args()

    data: Dict[Tuple[int, int], int] = {}

    f_type: Literal["json", "pickle"] = nbsp.type
    file_loc: str = nbsp.file
    token_loc: str = nbsp.token_file

    with open(file_loc, "rb" if f_type == "pickle" else "r") as f:
        if f_type == "json":
            for [x, y, c] in json.load(f):
                data[(x, y)] = c
        else:
            data = pickle.load(f)

    with open(token_loc) as f:
        tokens = json.load(f)

    logger.info(f"Loaded from {file_loc}!")
    logger.info(f"Loaded {len(tokens)} tokens from {token_loc}!")
    logger.info(f"Painting from {min(data.keys())} to {max(data.keys())}")

    asyncio.run(main(data, tokens))
