import logging
import queue
import threading
from collections.abc import Sequence
from typing import Callable

import cv2

from config.constants import LOG_LEVEL, LOG_FORMAT, QUEUE_SIZE, PRODUCER_THREAD_SEEMS_DEAD_TIMEOUT
from models.dto import BoundingBox, VideoFrame, ThreadingEvent
from models.errors import TrackingError

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

SAFETY_TIMEOUT = 0.3


class VideoFrameConsumerThread:
    tracker: cv2.Tracker
    object_id: int
    input_queue: queue.Queue[VideoFrame]
    output_queue: queue.Queue[BoundingBox]
    thread: threading.Thread
    should_quit: threading.Event
    error_callback: Callable

    def __init__(self, object_id: int, on_error_callback: Callable):
        """
        initialize object tracker thread, but do not run it yet.
        on_error will be called whenever there is an error which prevents this thread from continuing it's work.
        It should contain a method which deletes this object cleanly.
        :return: created tracker instance
        """
        self.tracker = cv2.TrackerMIL.create()
        self.object_id = object_id
        self.input_queue = queue.Queue(QUEUE_SIZE)
        self.output_queue = queue.Queue(QUEUE_SIZE)
        self.thread: threading.Thread = threading.Thread(target=self.run_tracking_loop)
        self.thread.daemon = True
        self.should_quit = threading.Event()
        self.error_callback = on_error_callback

    def on_error(self, message: str):
        """This method should be called whenever there is an error which means that this thread cannot continue its work.
        The error_callback should be set by the session-object which should handle the deletion of this object"""
        logger.error(message)
        e = ThreadingEvent(self.object_id, message)
        self.error_callback(e)

    def start(self, initial_bounding_box: BoundingBox):
        logger.debug(
            f"Starting video frame consumer thread for {initial_bounding_box.id} on frame {initial_bounding_box.frame_number}")
        frame: VideoFrame = self.input_queue.get()
        bounding_box_coordinates: tuple = (
            initial_bounding_box.x, initial_bounding_box.y, initial_bounding_box.width, initial_bounding_box.height)
        self.tracker.init(frame.img, bounding_box_coordinates)
        self.thread.start()

    def quit(self):
        self.should_quit.set()
        # only join if the thread has been started
        logger.debug(f"Video frame consumer thread exiting")

    def has_quit(self):
        return self.should_quit.is_set()

    def update_tracking(self, img):
        success, bounding_box = self.tracker.update(img)
        if success:
            return bounding_box
        else:
            logger.warning("Tracking failed")
            raise TrackingError("Tracking failed")

    def run_tracking_loop(self):
        """
        Run the tracking loop and fill the output_queue with tracking data
        """
        while not self.has_quit():
            try:
                frame = self.input_queue.get(timeout=PRODUCER_THREAD_SEEMS_DEAD_TIMEOUT)
                bounding_box: Sequence[int] = self.update_tracking(frame.img)
                self.output_queue.put(
                    BoundingBox(id=self.object_id, frame_number=frame.frame_number, x=bounding_box[0],
                                y=bounding_box[1],
                                width=bounding_box[2], height=bounding_box[3]))
                logger.debug(f"Tracker {self.object_id} processed frame {frame.frame_number}")
            except Exception as e:
                self.on_error(f"Video frame consumer error: {e}")
        self.read_queue_to_empty()
        logger.debug(f"Video frame consumer thread exited")

    def read_queue_to_empty(self):
        queue_is_empty = False
        while not queue_is_empty:
            try:
                self.input_queue.get(timeout=SAFETY_TIMEOUT)
            except queue.Empty:
                queue_is_empty = True

# Frames droppen um den neuen wieder zu bekommen
# numdropped = 0
# while pipe.poll:
#   pipe.receive
#   numdropped++
# return numdropped
