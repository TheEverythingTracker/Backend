#!/usr/bin/env python

import asyncio
import threading

from websockets import serve

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def main():
    async with serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever

def myrun():
    asyncio.run(main())

ws_thread = threading.Thread(target=myrun)
ws_thread.start()
while True:
    pass