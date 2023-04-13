from enum import Enum
from typing import List

from pydantic import BaseModel


class EventType(Enum, str):
    START_CONTROL_LOOP = "start-control-loop"
    CONTROL_LOOP_STARTED = "control-loop-started"
    ADD_OBJECT = "add-object"
    OBJECT_ADDED = "object-added"
    DELETE_OBJECT = "delete-object"
    OBJECT_DELETED = "object-deleted"
    UPDATE_TRACKING = "update-tracking"


class Event(BaseModel):
    event_type: EventType


class StartControlLoopEvent(Event):
    video_source: str  # todo validation?


class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class AddObjectEvent(Event):
    object_id: int  # todo int? uuid? ...?
    frame: int
    bounding_box: BoundingBox


# todo: events are basically the same... what do we do?
class ObjectAddedEvent(Event):
    id: int


class DeleteObjectEvent(Event):
    id: int


class ObjectDeletedEvent(Event):
    id: int


class UpdateTrackingEvent(Event):
    frame: int
    objects: List[BoundingBox]
