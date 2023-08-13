import queue

from fastapi import WebSocket

from models.dto import BoundingBox, UpdateTrackingEvent


class TrackingUpdateSenderThread:
    websocket: WebSocket
    input_queue: queue.Queue

    def __init__(self, websocket: WebSocket, input_queue: queue.Queue):
        self.websocket = websocket
        self.input_queue = input_queue

    def send(self):
        while True:
            bounding_box: BoundingBox = self.input_queue.get()
            update_tracking_event: UpdateTrackingEvent = UpdateTrackingEvent(frame_number=bounding_box.frame_number,
                                                                             bounding_boxes=list(bounding_box))
            self.websocket.send_json(update_tracking_event.model_dump_json())
            print(bounding_box.frame_number)
