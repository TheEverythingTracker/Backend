import logging
import queue
import threading

import cv2

from config.constants import LOG_FORMAT, LOG_LEVEL
from models.dto import VideoFrame

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class VideoFrameProducerThread:
    def __init__(self, video_source: str, queue_size: int):
        self.video_source: str = video_source
        self.stop: threading.Event = threading.Event()
        self.thread: threading.Thread = threading.Thread(target=self.read_video_frames)
        self.queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self.thread.start()

    def get_next_frame(self):
        # use timeout beacuse otherwise we would block forever if there are no new frames
        # 1 second timeout should be fine because reading a frame should be way faster than that
        return self.queue.get(timeout=1)

    def quit(self):
        self.stop.set()

    def has_quit(self):
        return self.stop.is_set()

    def join(self):
        self.thread.join()

    def read_video_frames(self):
        video_capture: cv2.VideoCapture = cv2.VideoCapture(self.video_source)
        frame_number: int = 0
        while True:
            if self.stop.is_set():
                return
            success, img = video_capture.read()
            if not success:
                video_capture.release()
                self.stop.set()
                return
            frame_number += 1
            self.queue.put(VideoFrame(frame_number=frame_number, frame=img))
            logger.debug(f"Frame {frame_number} read")
