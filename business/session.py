import asyncio
import logging
from queue import Empty
from uuid import UUID

from fastapi import WebSocket

from business.video_frame_producer import VideoFrameProducerThread
from config.constants import LOG_LEVEL, LOG_FORMAT, VIDEO_SOURCE
from models.dto import VideoFrame

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class Session:
    session_id: UUID
    websocket: WebSocket
    handler_tasks: list[asyncio.Task]
    video_frame_producer_thread: VideoFrameProducerThread

    def __init__(self, session_id: UUID, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.handler_tasks = []
        # todo: video_source should be read from event
        self.video_frame_producer_thread = VideoFrameProducerThread(VIDEO_SOURCE, 10)
        logger.debug(f"Session '{session_id}' created")

    def __del__(self):
        for task in self.handler_tasks:
            task.cancel()
        self.video_frame_producer_thread.quit()
        self.video_frame_producer_thread.join()
        logger.debug(f"Session '{self.session_id}' destroyed")

    async def start_event_handlers(self):
        self.handler_tasks.append(asyncio.create_task(self.__consume_websocket_events()))
        self.handler_tasks.append(asyncio.create_task(self.__produce_websocket_events()))
        done, pending = await asyncio.wait(self.handler_tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def __consume_websocket_events(self):
        logger.info(f"Session '{self.session_id}' started consuming events")
        async for message in self.websocket.iter_json():
            logger.debug(f"Session '{self.session_id}' received: {message}")
            # todo: handle events

    async def __produce_websocket_events(self):
        logger.info(f"Session '{self.session_id}' started producing events")
        # todo: wip: the frames should not be sent to websocket but given to the cv2-trackers
        while not self.video_frame_producer_thread.has_quit():
            try:
                frame: VideoFrame = self.video_frame_producer_thread.get_next_frame()
                await self.websocket.send_json({"frame": frame.frame_number})
                logger.debug(f"Session '{self.session_id}' has sent frame {frame.frame_number}")
                await asyncio.sleep(0)
            except Empty:
                logger.warning(f"Session '{self.session_id}': No frames to read")
        logger.info(f"Session '{self.session_id}' stopped producing events")
