import logging
import queue
import threading
import time

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
    should_quit: threading.Event
    thread: threading.Thread
    queues: list[queue.Queue[VideoFrame]]

    def __init__(self):
        self.should_quit = threading.Event()
        self.thread = threading.Thread(target=self.read_video_frames)
        self.queues = []

    def load(self, video_source: str):
        logger.debug(f"Loading {video_source}")
        if self.thread.is_alive():
            return
        self.video_source: str = video_source
        self.video_capture: cv2.VideoCapture = cv2.VideoCapture(self.video_source)
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        print("--- fps is " + str(self.fps) )

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
        # only join if the thread has been started
        if self.thread.ident is not None:
            self.thread.join()
        logger.debug(f"Video frame producer thread exited")

    def has_quit(self):
        return self.should_quit.is_set()

    def read_video_frames(self):
        frame_number: int = 0
        time_per_frame = 1.0 / self.fps

        while not self.has_quit():
            time_start = time.time()
            success, img = self.video_capture.read()
            if not success:
                self.should_quit.set()
            frame_number += 1

            # this blocks until the queue has a free slot
            for output_queue in self.queues:
                try:
                    output_queue.put(VideoFrame(frame_number=frame_number, img=img),timeout=time_per_frame)
                except queue.Full:
                    logger.debug("Queue is blocked, skipping frame " + str(frame_number))
            logger.debug(f"Frame {frame_number} read")

            print("Queue size: " + str(len(self.queues)))

            if(len(self.queues) == 0):
                print("sleeping for " + str(time_per_frame))
                time.sleep(time_per_frame)
           # finally:
             #   self.video_capture.release()
