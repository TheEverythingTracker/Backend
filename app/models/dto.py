from enum import Enum
from typing import List, Any, Optional
from uuid import UUID

from pydantic import BaseModel


class EventType(str, Enum):
    START_CONTROL_LOOP = "start-control-loop"
    ADD_BOUNDING_BOX = "add-bounding-box"
    DELETE_BOUNDING_BOX = "delete-bounding-boxes"
    UPDATE_TRACKING = "update-tracking"
    STOP_CONTROL_LOOP = "stop-control-loop"
    SUCCESS = "success"
    FAILURE = "failure"
    TRACKING_ERROR = "tracking-error"


class VideoFrame(BaseModel):
    frame_number: int
    img: Any


class Event(BaseModel):
    event_type: EventType


class TrackingErrorEvent(Event):
    message: str
    boundingBoxId: int


class IdEvent(Event):
    request_id: UUID


class StartControlLoopEvent(IdEvent):
    video_source: str  # todo validation?


class BoundingBox(BaseModel):
    id: int
    frame_number: Optional[int]
    x: int
    y: int
    width: int
    height: int


class AddBoundingBoxEvent(IdEvent):
    frame_number: int
    bounding_box: BoundingBox


class DeleteBoundingBoxesEvent(IdEvent):
    ids: List[int]


class UpdateTrackingEvent(Event):
    frame_number: int
    bounding_boxes: List[BoundingBox]


class StopControlLoopEvent(IdEvent):
    pass


class AnswerEvent(IdEvent):
    message: str


class SuccessEvent(AnswerEvent):
    pass


class FailureEvent(AnswerEvent):
    pass


class ThreadingEvent:
    source: int | str
    message: str

    def __init__(self, source: int | str, message: str):
        self.source = source
        self.message = message
