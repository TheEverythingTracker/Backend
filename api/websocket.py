import asyncio
import json
import logging
import multiprocessing

import websockets
from pydantic import parse_obj_as

from business.controller import Controller
from config.constants import LOG_LEVEL
from models import dto

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def _get_event_object_from_message(message):
    event: dict = json.loads(message)
    if event["event_type"] == dto.EventType.START_CONTROL_LOOP:
        return parse_obj_as(dto.StartControlLoopEvent, event)
    if event["event_type"] == dto.EventType.ADD_BOUNDING_BOX:
        return parse_obj_as(dto.AddBoundingBoxEvent, event)
    if event["event_type"] == dto.EventType.DELETE_BOUNDING_BOX:
        return parse_obj_as(dto.DeleteBoundingBoxesEvent, event)
    else:
        warning_message = f"event_type {event['event_type']} unknown"
        logger.warning(warning_message)
        raise ValueError(warning_message)


class WebSocketServer:
    # Hiermit beschränken wir uns auf einen Control-Loop und damit auf einen Client(Frontend)
    # -> Müsste also als Prozess gestartet werden und als Liste verwaltet werden, wenn wir mehrere Clients bedienen wollen

    websocket: websockets.WebSocketServerProtocol
    controller: Controller
    bounding_box_queue: multiprocessing.Queue

    def __init__(self):
        self.controller = None
        self.bounding_box_queue = multiprocessing.Queue(20)
        self.websocket = None

    async def __handle_event(self, message: str):  # todo: mit Frontend abstimmen, wie die JSON-Formate aussehen sollen
        # todo: parse message and get event type
        try:
            event: dto.IdEvent = _get_event_object_from_message(message)
            if event.event_type == dto.EventType.START_CONTROL_LOOP:
                answer = await self.start_control_loop(event)
            elif event.event_type == dto.EventType.ADD_BOUNDING_BOX:
                answer = await self.add_bounding_box(event)
            elif event.event_type == dto.EventType.DELETE_BOUNDING_BOX:
                answer = await self.delete_bounding_box(event)
            else:
                answer = dto.AnswerEvent(message="not implemented")  # todo: other idea?
        except ValueError as e:
            logger.warning(e)
            answer = dto.AnswerEvent(message=e)
        await self.send_message(answer)

    async def start_control_loop(self, event: dto.StartControlLoopEvent):
        if self.controller is not None:
            if self.controller.controller_thread.is_alive():
                answer = dto.SuccessEvent(event_type=dto.EventType.SUCCESS,
                                          message="Control loop already running!", request_id=event.request_id)
                await self.send_message(answer)
                logger.info("Control loop already running!")
                return
        logger.info("Starting control loop...")
        self.controller = Controller(event.video_source, self.bounding_box_queue)
        # todo: temporary workaround: start control loop only when we received the first bounding box
        # self.controller.run()
        # --------------------
        answer = dto.SuccessEvent(event_type=dto.EventType.SUCCESS,
                                  message="Control loop successfully started.", request_id=event.request_id)
        return answer

    async def add_bounding_box(self, event: dto.AddBoundingBoxEvent):
        self.controller.add_worker(event.bounding_box)
        self.controller.start_thread()
        answer = dto.SuccessEvent(event_type=dto.EventType.SUCCESS,
                                  message="Added bounding box successfully.", request_id=event.request_id)
        return answer

    async def delete_bounding_box(self, event: dto.DeleteBoundingBoxesEvent):
        self.controller.stop_workers(event.ids)
        answer = dto.SuccessEvent(event_type=dto.EventType.SUCCESS,
                                  message="Deleted bounding boxes successfully.", request_id=event.request_id)
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
