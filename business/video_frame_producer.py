import logging
import queue
import threading

import cv2

from config.constants import LOG_FORMAT, LOG_LEVEL, QUEUE_SIZE
from models.dto import VideoFrame

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class VideoFrameProducerThread:
    """Produce video frames. Does not support changing the video source"""
    video_source: str
    video_capture: cv2.VideoCapture

    def __init__(self):
        self.should_quit: threading.Event = threading.Event()
        self.thread: threading.Thread = threading.Thread(target=self.read_video_frames)
        self.queue: queue.Queue = queue.Queue(QUEUE_SIZE)

    def start(self, video_source: str):
        logger.debug(f"Starting video frame producer thread for {video_source}")
        if self.thread.is_alive():
            return
        self.video_source: str = video_source
        self.video_capture: cv2.VideoCapture = cv2.VideoCapture(self.video_source)
        self.thread.start()

    def get_next_frame(self):
        return self.queue.get()

    def quit(self):
        self.should_quit.set()
        # only join if the thread has been started
        if self.thread.ident is not None:
            self.thread.join()
        logger.debug(f"Video frame producer thread exited")

    def has_quit(self):
        return self.should_quit.is_set()

    def read_video_frames(self):
        frame_number: int = 0
        try:
            while not self.has_quit():
                success, img = self.video_capture.read()
                if not success:
                    self.should_quit.set()
                frame_number += 1
                # this blocks until the queue has a free slot
                self.queue.put(VideoFrame(frame_number=frame_number, img=img))
                logger.debug(f"Frame {frame_number} read")
        finally:
            self.video_capture.release()
