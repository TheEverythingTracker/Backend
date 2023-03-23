import asyncio
import queue

import websockets

bounding_box_queue = queue.Queue(20)


async def __producer_handler(websocket):
    print("producer_handler started")
    while True:
        message = bounding_box_queue.get()  # todo: discard frames if queue full?
        await websocket.send(message)


async def __run_websocket_server():
    async with websockets.serve(__producer_handler, "localhost", 8765):
        await asyncio.Future()


def start_websocket_server():
    """
    Start a server for sending the tracking data over websocket
    """
    asyncio.run(__run_websocket_server())
