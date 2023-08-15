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


class TrackingUpdateSenderThread:
    websocket: WebSocket
    input_queues: list[queue.Queue]
    thread: threading.Thread
    should_quit: threading.Event

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.input_queues = []
        self.should_quit = threading.Event()
        self.thread = threading.Thread(target=self.run_in_async_loop)

    def start(self):
        logger.debug(f"Starting tracking update sender thread")
        if self.thread.is_alive():
            return
        self.thread.start()

    def add_queue(self, input_queue: queue.Queue):
        self.input_queues.append(input_queue)

    def remove_queue(self, input_queue: queue.Queue):
        self.input_queues.remove(input_queue)

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

    async def send_updates(self):
        frame_number = -1
        while not self.has_quit():
            update_tracking_event: UpdateTrackingEvent = UpdateTrackingEvent(event_type=EventType.UPDATE_TRACKING,
                                                                             bounding_boxes=[],
                                                                             frame_number=frame_number)
            for input_queue in self.input_queues:
                bounding_box: BoundingBox = input_queue.get()
                update_tracking_event.bounding_boxes.append(bounding_box)
                frame_number = bounding_box.frame_number
            update_tracking_event.frame_number = frame_number
            # todo: might throw an exception if the session is closed, but this thread is still running
            await self.websocket.send_json(update_tracking_event.model_dump_json())
            logger.debug(f"UpdateTrackingEvent sent for frame {update_tracking_event.frame_number}")
