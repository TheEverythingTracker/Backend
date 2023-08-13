import logging
import queue
import threading
from collections.abc import Sequence

import cv2

from config.constants import LOG_LEVEL, LOG_FORMAT
from models.dto import BoundingBox, VideoFrame
from models.errors import TrackingError

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class TrackerThread:
    def __init__(self, object_id, input_queue: queue.Queue[VideoFrame], output_queue: queue.Queue):
        """
        initialize object tracker by object selection in first frame
        :return: created tracker instance
        """
        tracker = cv2.TrackerMIL.create()
        self.tracker = tracker
        self.object_id = object_id
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.thread: threading.Thread = threading.Thread(target=self.run_tracking_loop)
        self.should_quit = threading.Event()

    def start(self, initial_bounding_box: BoundingBox):
        frame: VideoFrame = self.input_queue.get()
        bounding_box_coordinates: tuple = (
            initial_bounding_box.x, initial_bounding_box.y, initial_bounding_box.width, initial_bounding_box.height)
        self.tracker.init(frame.img, bounding_box_coordinates)
        self.thread.start()

    def quit(self):
        self.should_quit.set()
        self.thread.join()

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
            frame = self.input_queue.get()
            bounding_box: Sequence[int] = self.update_tracking(frame.img)
            self.output_queue.put(
                BoundingBox(id=self.object_id, frame_number=frame.frame_number, x=bounding_box[0], y=bounding_box[1],
                            width=bounding_box[2], height=bounding_box[3]))

# Frames droppen um den neuen wieder zu bekommen
# numdropped = 0
# while pipe.poll:
#   pipe.receive
#   numdropped++
# return numdropped
