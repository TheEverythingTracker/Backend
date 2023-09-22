import logging
import queue
import threading
from typing import Callable

import cv2

from app.config.constants import LOG_FORMAT, LOG_LEVEL
from app.models.dto import VideoFrame, ThreadingEvent

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
    quit_callback: Callable

    def __init__(self, on_quit_callback: Callable):
        self.should_quit = threading.Event()
        self.thread = threading.Thread(target=self.read_video_frames)
        self.thread.daemon = True
        self.queues = []
        self.quit_callback = on_quit_callback

    def on_quit(self, message: str):
        """This method should be called whenever there is an error which means that this thread cannot continue its work.
        The error_callback should be set by the session-object which should handle the deletion of this object"""
        logger.info(message)
        e = ThreadingEvent(self.video_source, message)
        self.quit_callback(e)

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
        total_frames = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
        try:
            while not self.has_quit():
                success, img = self.video_capture.read()
                if not success:
                    if frame_number >= total_frames:
                        self.on_quit("Video frame producer finished")
                        return
                    else:
                        self.on_quit(f"Video frame producer could not read next frame. exiting")
                        return
                frame_number += 1
                # this blocks until the queue has a free slot
                if self.queues:
                    for output_queue in self.queues:
                        output_queue.put(VideoFrame(frame_number=frame_number, img=img))
                        logger.debug(f"Frame {frame_number} of {total_frames} read")
                else:
                    threading.Event().wait(1 / fps)
                    logger.debug(f"Frame {frame_number} of {total_frames} ignored")
        finally:
            self.video_capture.release()
            logger.debug(f"Video frame producer thread exited")
