from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel


class EventType(str, Enum):
    START_CONTROL_LOOP = "start-control-loop"
    ADD_BOUNDING_BOX = "add-bounding-box"
    DELETE_BOUNDING_BOX = "delete-bounding-box"
    UPDATE_TRACKING = "update-tracking"
    STOP_CONTROL_LOOP = "stop-control-loop"
    SUCCESS = "success"
    FAILURE = "failure"


class Event(BaseModel):
    event_type: EventType
    request_id: UUID


class StartControlLoopEvent(Event):
    video_source: str  # todo validation?


class BoundingBox(BaseModel):
    id: int
    x: int
    y: int
    width: int
    height: int


class AddBoundingBoxEvent(Event):
    frame: int
    bounding_box: BoundingBox


class DeleteBoundingBoxesEvent(Event):
    ids: List[int]


class UpdateTrackingEvent(Event):
    frame: int
    bounding_boxes: List[BoundingBox]


class StopControlLoopEvent(Event):
    pass


class AnswerEvent(Event):
    message: str


class SuccessEvent(AnswerEvent):
    pass


class FailureEvent(AnswerEvent):
    pass
