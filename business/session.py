import logging
from uuid import UUID

from fastapi import WebSocket
import asyncio

from config.constants import LOG_LEVEL, LOG_FORMAT

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class Session:
    session_id: UUID
    websocket: WebSocket
    websocket_handler_tasks: list[asyncio.Task]

    def __init__(self, session_id: UUID, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.websocket_handler_tasks = []
        logger.debug(f"Session '{session_id}' created")

    def __del__(self):
        for task in self.websocket_handler_tasks:
            task.cancel()
        logger.debug(f"Session '{self.session_id}' destroyed")

    async def start_handlers(self):
        self.websocket_handler_tasks.append(asyncio.create_task(self.__consume_websocket_events()))
        self.websocket_handler_tasks.append(asyncio.create_task(self.__produce_websocket_events()))
        done, pending = await asyncio.wait(self.websocket_handler_tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def __consume_websocket_events(self):
        logger.info(f"Session '{self.session_id}' started consuming events")
        async for message in self.websocket.iter_json():
            logger.debug(f"Session '{self.session_id}' received: {message}")
            # todo handle event

    async def __produce_websocket_events(self):
        logger.info(f"Session '{self.session_id}' started producing events")
        # todo: correct implementation
        await self.__dummy_impl()

    async def __dummy_impl(self):
        """Dummy implementation for testing purposes. Sends an event to websokcet every 3 seconds."""
        messages = 0

        while True:
            messages += 1
            await asyncio.sleep(3)
            await self.websocket.send_json({"message_no": messages, "message": "See you in 3 seconds!"})
