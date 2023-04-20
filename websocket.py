import asyncio
import json
import multiprocessing
import threading

import websockets
from pydantic import parse_obj_as

import dto
from main import run_control_loop


def _get_event_object_from_message(message):
    event: dict = json.loads(message)
    if event["event-type"] == dto.EventType.START_CONTROL_LOOP:
        return parse_obj_as(dto.StartControlLoopEvent, event)
    if event["event-type"] == dto.EventType.ADD_BOUNDING_BOX:
        return parse_obj_as(dto.AddBoundingBoxEvent, event)


class WebSocketServer:
    # Hiermit beschränken wir uns auf einen Control-Loop und damit auf einen Client(Frontend)
    # -> Müsste also als Prozess gestartet werden und als Liste verwaltet werden, wenn wir mehrere Clients bedienen wollen

    websocket: websockets.WebSocketServerProtocol
    control_loop_thread: threading.Thread
    bounding_box_queue: multiprocessing.Queue

    def __init__(self):
        self.control_loop_thread = None
        self.bounding_box_queue = multiprocessing.Queue(20)
        self.websocket = None

    async def __handle_event(self, message: str):  # todo: mit Frontend abstimmen, wie die JSON-Formate aussehen sollen
        # todo: parse message and get event type
        print(f"Handling event for message {message}")
        event: dto.Event = _get_event_object_from_message(message)
        if event.event_type == dto.EventType.START_CONTROL_LOOP:
            answer = await self.start_control_loop()
        else:
            answer = dto.AnswerEvent(message="Event unknown. Something went wrong.")
        await self.send_message(answer)

    async def start_control_loop(self):
        if self.control_loop_thread is not None:
            if self.control_loop_thread.is_alive():
                answer = dto.ControlLoopStartedEvent(event_type=dto.EventType.CONTROL_LOOP_STARTED,
                                                     message="Control loop already running!")
                await self.send_message(answer)
                print("Control loop already running!")
                return
        print("Starting control loop...")
        self.control_loop_thread = threading.Thread(target=run_control_loop, args=(True, self.bounding_box_queue))
        self.control_loop_thread.start()
        answer = dto.ControlLoopStartedEvent(event_type=dto.EventType.CONTROL_LOOP_STARTED,
                                             message="Control loop successfully started.")
        return answer

    async def __consumer_handler(self, websocket):
        print("consumer_handler started")
        async for message in websocket:
            print(f"received message: {message}")
            await self.__handle_event(message)

    async def __producer_handler(self, websocket):
        print("producer_handler started")
        while True:
            # todo: discard frames if queue full?
            loop = asyncio.get_running_loop()
            message = await loop.run_in_executor(None, self.bounding_box_queue.get)
            print(f"producer_handler: sending {message}")
            await websocket.send(message.json(by_alias=True))
            # If you run a loop that contains only synchronous operations and a send() call,
            # you must yield control explicitly with asyncio.sleep():
            # https://websockets.readthedocs.io/en/stable/faq/asyncio.html
            # todo vielleicht brauchen wir das nicht mehr, weil wir jetzt asynchron in einem thread auf das nächste Ergebnis der Queue warten und die Kontrolle abgeben
            await asyncio.sleep(0)

    async def __handler(self, websocket):
        self.websocket = websocket
        consumer_task = asyncio.create_task(self.__consumer_handler(websocket))
        producer_task = asyncio.create_task(self.__producer_handler(websocket))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    async def send_message(self, message: dto.AnswerEvent):
        await self.websocket.send(message.json(by_alias=True))

    async def run(self):
        async with websockets.serve(self.__handler, "localhost", 8765):
            await asyncio.Future()
