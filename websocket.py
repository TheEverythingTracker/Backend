import asyncio
import json
import logging
import multiprocessing
import threading
import uuid

import websockets
from pydantic import parse_obj_as

import dto
from constants import LOG_LEVEL
from main import run_control_loop


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def _get_event_object_from_message(message):
    event: dict = json.loads(message)
    if event["event_type"] == dto.EventType.START_CONTROL_LOOP:
        return parse_obj_as(dto.StartControlLoopEvent, event)
    if event["event_type"] == dto.EventType.ADD_BOUNDING_BOX:
        return parse_obj_as(dto.AddBoundingBoxEvent, event)
    else:
        warning_message = f"event_type {event['event_type']} unknown"
        logger.warning(warning_message)
        raise ValueError(warning_message)


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
        try:
            event: dto.IdEvent = _get_event_object_from_message(message)
            if event.event_type == dto.EventType.START_CONTROL_LOOP:
                answer = await self.start_control_loop(event.request_id)
            else:
                answer = dto.AnswerEvent(message="not implemented")  # todo: other idea?
        except ValueError as e:
            logger.warning(e)
            answer = dto.AnswerEvent(message=e)
        await self.send_message(answer)

    async def start_control_loop(self, request_id: uuid.UUID):
        if self.control_loop_thread is not None:
            if self.control_loop_thread.is_alive():
                answer = dto.SuccessEvent(event_type=dto.EventType.SUCCESS,
                                          message="Control loop already running!", request_id=request_id)
                await self.send_message(answer)
                logger.info("Control loop already running!")
                return
        logger.info("Starting control loop...")
        self.control_loop_thread = threading.Thread(target=run_control_loop, args=(True, self.bounding_box_queue))
        self.control_loop_thread.start()
        answer = dto.SuccessEvent(event_type=dto.EventType.SUCCESS,
                                  message="Control loop successfully started.", request_id=request_id)
        return answer

    async def __consumer_handler(self, websocket):
        logger.info("consumer_handler started")
        async for message in websocket:
            logger.debug(f"received message: {message}")
            await self.__handle_event(message)

    async def __producer_handler(self):
        logger.info("producer_handler started")
        while True:
            # todo: discard frames if queue full?
            loop = asyncio.get_running_loop()
            message = await loop.run_in_executor(None, self.bounding_box_queue.get)
            logger.debug(f"producer_handler: sending {message}")
            await self.send_message(message)
            # If you run a loop that contains only synchronous operations and a send() call,
            # you must yield control explicitly with asyncio.sleep():
            # https://websockets.readthedocs.io/en/stable/faq/asyncio.html
            # todo vielleicht brauchen wir das nicht mehr, weil wir jetzt asynchron in einem thread auf das nächste Ergebnis der Queue warten und die Kontrolle abgeben
            await asyncio.sleep(0)

    async def __handler(self, websocket):
        self.websocket = websocket
        consumer_task = asyncio.create_task(self.__consumer_handler(websocket))
        producer_task = asyncio.create_task(self.__producer_handler())
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    async def send_message(self, message: dto.AnswerEvent):
        logger.debug(f"send message. {message}")
        await self.websocket.send(message.json())

    async def run(self):
        async with websockets.serve(self.__handler, "localhost", 8765):
            await asyncio.Future()
