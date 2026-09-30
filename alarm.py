import asyncio
import json
import os
import time

import aiohttp
import websockets

SYMBOL = os.getenv("SYMBOL", "MSFTUSDT").upper()
LOW_PRICE = float(os.getenv("LOW_PRICE", "76"))
HIGH_PRICE = float(os.getenv("HIGH_PRICE", "88"))
ALARM_REPEAT_SECONDS = int(os.getenv("ALARM_REPEAT_SECONDS", "60"))
MESSAGE_TIMEOUT = int(os.getenv("MESSAGE_TIMEOUT", "15"))
RECONNECT_DELAY = int(os.getenv("RECONNECT_DELAY", "5"))

WEBHOOK_URL = os.environ["MACRODROID_WEBHOOK"]

WS_URL = (
    "wss://fstream.binance.com/market/ws/"
    f"{SYMBOL.lower()}@markPrice@1s"
)

last_alarm = 0.0


async def trigger_alarm(price: float, direction: str) -> None:
    print(
        f"!!! ALARM: {SYMBOL} {direction} threshold, price={price:.4f}",
        flush=True,
    )

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(WEBHOOK_URL) as response:
                body = await response.text()
                print(
                    f"MacroDroid response: {response.status} {body[:120]!r}",
                    flush=True,
                )
    except Exception as exc:
        print(f"Webhook error: {exc}", flush=True)


async def monitor() -> None:
    global last_alarm

    if LOW_PRICE >= HIGH_PRICE:
        raise ValueError("LOW_PRICE must be lower than HIGH_PRICE")

    print(
        f"Monitoring {SYMBOL}: alarm below {LOW_PRICE} or above {HIGH_PRICE}",
        flush=True,
    )

    while True:
        try:
            print(f"{SYMBOL}: connecting to Binance...", flush=True)

            async with websockets.connect(
                WS_URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
            ) as ws:
                print(f"{SYMBOL}: connected.", flush=True)

                while True:
                    try:
                        message = await asyncio.wait_for(
                            ws.recv(),
                            timeout=MESSAGE_TIMEOUT,
                        )
                    except asyncio.TimeoutError as exc:
                        raise ConnectionError(
                            f"No {SYMBOL} updates for {MESSAGE_TIMEOUT} seconds"
                        ) from exc

                    data = json.loads(message)
                    price = float(data["p"])
                    print(f"{SYMBOL}: {price:.4f}", flush=True)

                    direction = None
                    if price < LOW_PRICE:
                        direction = "BELOW"
                    elif price > HIGH_PRICE:
                        direction = "ABOVE"

                    if direction is not None:
                        now = time.time()
                        if now - last_alarm >= ALARM_REPEAT_SECONDS:
                            await trigger_alarm(price, direction)
                            last_alarm = now
                    else:
                        # Back inside the safe range: the next threshold break
                        # must alarm immediately.
                        last_alarm = 0.0

        except Exception as exc:
            print(f"{SYMBOL} connection error: {exc}", flush=True)
            print(
                f"{SYMBOL}: reconnecting in {RECONNECT_DELAY} seconds...",
                flush=True,
            )
            await asyncio.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    asyncio.run(monitor())
