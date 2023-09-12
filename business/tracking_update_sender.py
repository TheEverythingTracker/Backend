import asyncio
import logging
import queue
import threading

from fastapi import WebSocket

from config.constants import LOG_FORMAT, LOG_LEVEL
from models.dto import BoundingBox, UpdateTrackingEvent
from models.dto import EventType

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class QueueWrapper:
    input_queue: queue.Queue
    latest_bounding_box: BoundingBox
    latest_frame: int

    def __init__(self, input_queue: queue.Queue):
        self.input_queue = input_queue
        self.latest_bounding_box = None
        self.latest_frame = -1


class TrackingUpdateSenderThread:
    websocket: WebSocket
    update_queue_items: list[QueueWrapper]
    thread: threading.Thread
    should_quit: threading.Event

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.update_queue_items = []
        self.should_quit = threading.Event()
        self.thread = threading.Thread(target=self.run_in_async_loop)
        self.thread.daemon = True

    def start(self):
        logger.debug(f"Starting tracking update sender thread")
        self.thread.start()

    def is_running(self):
        return self.thread.is_alive()

    def add_queue(self, input_queue: queue.Queue):
        self.update_queue_items.append(QueueWrapper(input_queue))

    def remove_queue(self, input_queue: queue.Queue):
        temp_list = self.update_queue_items.copy()
        for item in temp_list:
            if item.input_queue is input_queue:
                self.update_queue_items.remove(item)

    def quit(self):
        self.should_quit.set()
        logger.debug(f"Tracking update sender thread exiting")

    def has_quit(self):
        return self.should_quit.is_set()

    def run_in_async_loop(self):
        # https://stackoverflow.com/questions/59645272/how-do-i-pass-an-async-function-to-a-thread-target-in-python
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.send_updates())
        loop.close()

    def get_current_max_frame_number(self):
        max_frame_number: int = -1
        for item in self.update_queue_items:
            if item.latest_frame > max_frame_number:
                max_frame_number = item.latest_frame
        return max_frame_number

    async def send_updates(self):
        while not self.has_quit():
            if len(self.update_queue_items) != 0:
                bounding_boxes: list[BoundingBox] = []

                for index, update_queue_item in enumerate(self.update_queue_items):
                    # here the update sender stops trackers from tracking
                    update_queue_item.latest_bounding_box = update_queue_item.input_queue.get()
                    update_queue_item.latest_frame = update_queue_item.latest_bounding_box.frame_number

                max_frame_number: int = self.get_current_max_frame_number()
                for update_queue_item in self.update_queue_items:
                    while not update_queue_item.latest_frame == max_frame_number:
                        update_queue_item.latest_bounding_box = update_queue_item.input_queue.get()
                        update_queue_item.latest_frame = update_queue_item.latest_bounding_box.frame_number
                    bounding_boxes.append(update_queue_item.latest_bounding_box)

                for index, bounding_box in enumerate(bounding_boxes):
                    logger.debug(f"Sending bounding box {bounding_box.frame_number} from queue {index}")

                update_tracking_event: UpdateTrackingEvent = UpdateTrackingEvent(event_type=EventType.UPDATE_TRACKING,
                                                                                 bounding_boxes=bounding_boxes,
                                                                                 frame_number=max_frame_number)
                # todo: might throw an exception if the session is closed, but this thread is still running
                await self.websocket.send_json(update_tracking_event.model_dump_json())
                logger.debug(f"UpdateTrackingEvent sent for frame {update_tracking_event.frame_number}")
        logger.debug(f"Tracking update sender thread exited")
