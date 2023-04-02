import asyncio
import multiprocessing

import websockets

bounding_box_queue = multiprocessing.Queue(20)


async def __consumer_handler(websocket):
    print("producer_handler started")
    while True:
        message = bounding_box_queue.get()  # todo: discard frames if queue full?
        await websocket.send(message)
        # If you run a loop that contains only synchronous operations and a send() call,
        # you must yield control explicitly with asyncio.sleep():
        # https://websockets.readthedocs.io/en/stable/faq/asyncio.html
        await asyncio.sleep(0)


async def run_websocket_server():
    async with websockets.serve(__consumer_handler, "localhost", 8765):
        await asyncio.Future()


def start_websocket_server():
    """
    Start a server for sending the tracking data over websocket
    """
    asyncio.run(run_websocket_server())
