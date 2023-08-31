import asyncio
import logging
import queue
import threading
import time

from fastapi import WebSocket

from config.constants import LOG_FORMAT, LOG_LEVEL, SENDER_QUEUE_TIMEOUT
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
                print("---Trying to delete ferom sende--")
                self.update_queue_items.remove(item)
                print("---Delted  to delete ferom sende--")


    def quit(self):
        self.should_quit.set()
        # only join if the thread has been started
        if self.thread.ident is not None:
            self.thread.join()
        logger.debug(f"Tracking update sender thread exited")

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

    def print_bounding_boxes(self, bounding_boxes):
        for index, bounding_box in enumerate(bounding_boxes):
            frame_num = bounding_box.frame_number if bounding_box is not None else "NONE"
            logger.debug(f"Sending bounding box {frame_num} from queue {index}")

    async def send_updates(self):
        while not self.has_quit():
            bounding_boxes: list[BoundingBox] = []

            for index, update_queue_item in enumerate(self.update_queue_items):
                # here the update sender stops trackers from tracking
                try:
                    update_queue_item.latest_bounding_box = update_queue_item.input_queue.get(timeout=SENDER_QUEUE_TIMEOUT)
                    update_queue_item.latest_frame = update_queue_item.latest_bounding_box.frame_number
                except queue.Empty:
                    logger.debug("could not fetch frame from consumer output - skipped")

            max_frame_number: int = self.get_current_max_frame_number()
            for update_queue_item in self.update_queue_items:
                skipped_queue = False
                while not update_queue_item.latest_frame == max_frame_number and not skipped_queue:
                    try:
                        update_queue_item.latest_bounding_box = update_queue_item.input_queue.get(timeout=SENDER_QUEUE_TIMEOUT)
                        update_queue_item.latest_frame = update_queue_item.latest_bounding_box.frame_number
                    except queue.Full:
                        skipped_queue = True
                        logger.debug("could not fetch frame from consumer output - skipped")
                if not skipped_queue:
                    bounding_boxes.append(update_queue_item.latest_bounding_box)

            self.print_bounding_boxes(bounding_boxes)



            # todo: might throw an exception if the session is closed, but this thread is still running
            if len(bounding_boxes) > 0:
                update_tracking_event: UpdateTrackingEvent = UpdateTrackingEvent(event_type=EventType.UPDATE_TRACKING,
                                                                                 bounding_boxes=bounding_boxes,
                                                                                 frame_number=max_frame_number)
                await self.websocket.send_json(update_tracking_event.model_dump_json())
               # logger.debug(f"UpdateTrackingEvent sent for frame {update_tracking_event.frame_number}")
