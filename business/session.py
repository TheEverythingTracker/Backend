import logging
import queue
from uuid import UUID

from fastapi import WebSocket

from business.tracking_update_sender import TrackingUpdateSenderThread
from business.video_frame_consumer import VideoFrameConsumerThread
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
    video_frame_producer: VideoFrameProducerThread
    video_frame_consumers: list[VideoFrameConsumerThread]
    tracking_update_sender: TrackingUpdateSenderThread

    def __init__(self, session_id: UUID, websocket: WebSocket):
        self.session_id = session_id
        self.websocket = websocket
        self.video_frame_producer = VideoFrameProducerThread()
        self.video_frame_consumers = []
        self.tracking_update_sender = TrackingUpdateSenderThread(self.websocket)
        logger.debug(f"Session '{session_id}' created")

    def __del__(self):
        logger.debug(f"Destroying Session '{self.session_id}'")
        self.video_frame_producer.quit()
        for consumer in self.video_frame_consumers:
            consumer.quit()
        self.tracking_update_sender.quit()
        logger.debug(f"Session '{self.session_id}' destroyed")

    def start_control_loop(self, event: dto.StartControlLoopEvent):
        self.video_frame_producer.load(video_source=event.video_source)
        return dto.SuccessEvent(event_type=EventType.SUCCESS, request_id=event.request_id, message="OK.")

    def add_bounding_box(self, event: dto.AddBoundingBoxEvent):
        video_frame_consumer = VideoFrameConsumerThread(event.bounding_box.id)
        self.video_frame_producer.add_queue(video_frame_consumer.input_queue)
        if not self.video_frame_producer.is_running():
            self.video_frame_producer.start()
        video_frame_consumer.start(event.bounding_box)
        self.tracking_update_sender.add_queue(video_frame_consumer.output_queue)
        if not self.tracking_update_sender.is_running():
            self.tracking_update_sender.start()
        self.video_frame_consumers.append(video_frame_consumer)
        return dto.SuccessEvent(event_type=EventType.SUCCESS, request_id=event.request_id, message="OK.")

    def delete_bounding_box(self, event: dto.DeleteBoundingBoxesEvent):
        for object_id in event.ids:
            consumer = self.video_frame_consumers[object_id]
            consumer.quit()
            self.video_frame_producer.remove_queue(consumer.input_queue)
            self.tracking_update_sender.remove_queue(consumer.output_queue)
            self.video_frame_consumers.remove(consumer)
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
        except Exception as e:
            logger.error(e)
            logger.info(f"Session '{self.session_id}' stopped consuming events")
            raise e

    async def __handle_event(self, message: dict):  # todo: mit Frontend abstimmen, wie die JSON-Formate aussehen sollen
        answer: dto.AnswerEvent
        if message['event_type'] == dto.EventType.START_CONTROL_LOOP:
            answer = self.start_control_loop(dto.StartControlLoopEvent.model_validate(message))
        elif message['event_type'] == dto.EventType.ADD_BOUNDING_BOX:
            answer = self.add_bounding_box(dto.AddBoundingBoxEvent.model_validate(message))
        elif message['event_type'] == dto.EventType.DELETE_BOUNDING_BOX:
            answer = self.delete_bounding_box(dto.DeleteBoundingBoxesEvent.model_validate(message))
        else:
            raise ValueError(f"Unknown event type '{message['event_type']}'")
        logger.debug(f"Session '{self.session_id}' handled {message['event_type']}")
        return answer
