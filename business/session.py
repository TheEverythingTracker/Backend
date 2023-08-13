import asyncio
import logging
import threading
from queue import Empty
from uuid import UUID

from fastapi import WebSocket

from business.video_frame_producer import VideoFrameProducerThread
from config.constants import LOG_LEVEL, LOG_FORMAT, VIDEO_SOURCE
from models import dto
from models.dto import VideoFrame

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class Session:
    session_id: UUID
    websocket: WebSocket
    handler_tasks: list[asyncio.Task]
    video_frame_producer_thread: VideoFrameProducerThread
    tracker_thread: threading.Thread  # todo: das muss eine liste werden

    def __init__(self, session_id: UUID, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.handler_tasks = []
        # todo: video_source should be read from event
        self.video_frame_producer_thread = VideoFrameProducerThread(300)
        logger.debug(f"Session '{session_id}' created")

    def __del__(self):
        for task in self.handler_tasks:
            task.cancel()
        self.video_frame_producer_thread.quit()
        self.video_frame_producer_thread.join()
        logger.debug(f"Session '{self.session_id}' destroyed")

    def start_control_loop(self, event: dto.StartControlLoopEvent):
        self.video_frame_producer_thread.start(video_source=event.video_source)
        return dto.AnswerEvent(message="OK.")

    async def start_event_handlers(self):
        # todo: da geht was in den handlern nicht :(
        self.handler_tasks.append(asyncio.create_task(self.__consume_websocket_events()))
        self.handler_tasks.append(asyncio.create_task(self.__produce_websocket_events()))
        done, pending = await asyncio.wait(self.handler_tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    async def __consume_websocket_events(self):
        logger.info(f"Session '{self.session_id}' started consuming events")
        while True:
            message = await self.websocket.receive_json()
            logger.debug(f"Session '{self.session_id}' received: {message}")
            answer = await self.__handle_event(message)
            logger.debug(f"Session '{self.session_id}' answering: {answer}")
            await self.websocket.send_json(answer.model_dump_json())

    async def __handle_event(self, message: dict):  # todo: mit Frontend abstimmen, wie die JSON-Formate aussehen sollen
        answer: dto.AnswerEvent
        print("hallo")
        if message['event_type'] == dto.EventType.START_CONTROL_LOOP:
            answer = self.start_control_loop(dto.StartControlLoopEvent.model_validate(message))
        elif message['event_type'] == dto.EventType.ADD_BOUNDING_BOX:
            answer = await self.add_bounding_box(dto.AddBoundingBoxEvent.model_validate(message))
        elif message['event_type'] == dto.EventType.DELETE_BOUNDING_BOX:
            answer = await self.delete_bounding_box(dto.DeleteBoundingBoxesEvent.model_validate(message))
        else:
            raise ValueError(f"Unknown event type '{message['event_type']}'")
        logger.debug(f"Session '{self.session_id}' handled {message['event_type']}")
        return answer

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
                pass
        logger.info(f"Session '{self.session_id}' stopped producing events")
