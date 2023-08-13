import logging
from uuid import UUID

from fastapi import WebSocket

from business.video_frame_producer import VideoFrameProducerThread
from config.constants import LOG_LEVEL, LOG_FORMAT
from models import dto
from models.dto import EventType

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class Session:
    session_id: UUID
    websocket: WebSocket
    video_frame_producer_thread: VideoFrameProducerThread

    def __init__(self, session_id: UUID, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.video_frame_producer_thread = VideoFrameProducerThread(10)
        logger.debug(f"Session '{session_id}' created")

    def __del__(self):
        self.video_frame_producer_thread.quit()
        self.video_frame_producer_thread.join()
        logger.debug(f"Session '{self.session_id}' destroyed")

    def start_control_loop(self, event: dto.StartControlLoopEvent):
        self.video_frame_producer_thread.start(video_source=event.video_source)
        return dto.SuccessEvent(event_type=EventType.SUCCESS, request_id=event.request_id, message="OK.")

    async def consume_websocket_events(self):
        try:
            logger.info(f"Session '{self.session_id}' started consuming events")
            while True:
                message = await self.websocket.receive_json()
                logger.debug(f"Session '{self.session_id}' received: {message}")
                answer = await self.__handle_event(message)
                logger.debug(f"Session '{self.session_id}' answering: {answer}")
                await self.websocket.send_json(answer.model_dump_json())
                logger.info(f"Session '{self.session_id}' stopped consuming events")
        except Exception as e:
            logger.error(e)
            raise e

    async def __handle_event(self, message: dict):  # todo: mit Frontend abstimmen, wie die JSON-Formate aussehen sollen
        answer: dto.AnswerEvent
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
