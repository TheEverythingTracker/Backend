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
    """Produce video frames. Does not support changing the video source"""
    video_source: str
    video_capture: cv2.VideoCapture
    should_quit: threading.Event
    thread: threading.Thread
    queues: list[queue.Queue[VideoFrame]]

    def __init__(self):
        self.should_quit = threading.Event()
        self.thread = threading.Thread(target=self.read_video_frames)
        self.thread.daemon = True
        self.queues = []

    def load(self, video_source: str):
        logger.debug(f"Loading {video_source}")
        if self.thread.is_alive():
            return
        self.video_source: str = video_source
        self.video_capture: cv2.VideoCapture = cv2.VideoCapture(self.video_source)

    def start(self):
        self.thread.start()

    def is_running(self):
        return self.thread.is_alive()

    def add_queue(self, output_queue: queue.Queue[VideoFrame]):
        self.queues.append(output_queue)

    def remove_queue(self, queue_to_remove: queue.Queue[VideoFrame]):
        self.queues.remove(queue_to_remove)

    def quit(self):
        self.should_quit.set()
        logger.debug(f"Video frame producer thread exiting")

    def has_quit(self):
        return self.should_quit.is_set()

    def read_video_frames(self):
        frame_number: int = 0
        fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        try:
            while not self.has_quit():
                success, img = self.video_capture.read()
                if not success:
                    self.should_quit.set()
                frame_number += 1
                # this blocks until the queue has a free slot
                if self.queues:
                    for output_queue in self.queues:
                        output_queue.put(VideoFrame(frame_number=frame_number, img=img))
                        logger.debug(f"Frame {frame_number} read")

                else:
                    threading.Event().wait(1 / fps)
                    logger.debug(f"No consumers: Frame {frame_number} ignored")
        finally:
            self.video_capture.release()
            logger.debug(f"Video frame producer thread exited")
