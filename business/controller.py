import logging
import multiprocessing
import queue
import threading
from typing import List

import cv2

from business.debug import show_debug_output
from business.worker.worker import WorkerProcess
from config.constants import LOG_LEVEL
from models import dto
from models.errors import OutOfResourcesError

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class Controller:
    num_cores: int
    video_source: str
    should_quit: bool
    workers: List[WorkerProcess]
    bounding_boxes_to_websocket_queue: multiprocessing.Queue
    bounding_boxes_from_workers_queue: multiprocessing.Queue
    controller_thread: threading.Thread

    def __init__(self, video_source: str, bounding_boxes_to_websocket_queue: multiprocessing.Queue):
        self.num_cores = multiprocessing.cpu_count()
        self.video_source = video_source
        self.should_quit = False
        self.workers = []
        self.bounding_boxes_to_websocket_queue = bounding_boxes_to_websocket_queue
        self.bounding_boxes_from_workers_queue = multiprocessing.Queue()
        self.controller_thread = None

    def add_worker(self, bounding_box: dto.BoundingBox):  # , frame):  # todo: frame should be numpy ndarray?
        # ----- temporary workaround: get frame as parameter -------
        cap = cv2.VideoCapture(self.video_source)
        success, img = cap.read()
        cap.release()
        # ----------------------------------
        if len(self.workers) <= self.num_cores:
            worker_process: WorkerProcess = WorkerProcess(img, (
                bounding_box.x, bounding_box.y, bounding_box.width, bounding_box.height),
                                                          self.bounding_boxes_from_workers_queue, bounding_box.id)
            self.workers.append(worker_process)
            logger.info(f"worker {worker_process.worker_id} started")
        else:
            logger.warning("not enough cpu cores")
            raise OutOfResourcesError("not enough cpu cores")

    def stop_workers(self, ids: List[int]):
        for worker in self.workers:
            if worker.worker_id in ids:
                worker.should_exit.set()
        # __run takes care of removing stopped workers

    def start_thread(self):
        if self.controller_thread and self.controller_thread.is_alive():
            return
        self.controller_thread = threading.Thread(target=self.__run)
        self.controller_thread.start()

    def stop_thread(self):
        self.should_quit = True
        self.controller_thread.join()
        self.controller_thread = None

    def __run(self):
        video_capture: cv2.VideoCapture = cv2.VideoCapture(self.video_source)
        # todo: is there a better way to get frame numbers?
        frame_number: int = 0
        while not self.should_quit:
            print(frame_number)
            success, img = video_capture.read()  # todo: errorhandling
            frame_number += 1
            tracking_event: dto.UpdateTrackingEvent = dto.UpdateTrackingEvent(event_type=dto.EventType.UPDATE_TRACKING,
                                                                              frame=frame_number, bounding_boxes=[])
            # todo: this loop will block until all workers have processed the current frame --> might be a performance bottleneck
            for w in self.workers.copy():
                if w.should_exit.is_set():
                    self.__remove_worker(w)
                else:
                    w.sender.send(img)
                try:
                    bounding_box: dto.BoundingBox = self.bounding_boxes_from_workers_queue.get(block=False)
                    # todo: asynchronous?
                    tracking_event.bounding_boxes.append(bounding_box)
                except queue.Empty:
                    logger.debug("empty queue")
            logger.debug(tracking_event.bounding_boxes)
            # todo: do not send empty tracking events
            self.bounding_boxes_to_websocket_queue.put(tracking_event)
            try:
                show_debug_output(img, tracking_event.bounding_boxes)
            except Exception:
                logger.debug("Debug Output failed")

        # Cleanup
        video_capture.release()
        self.should_quit = False
        logger.info("Goodbye!")

    def __remove_worker(self, w: WorkerProcess):
        w.process.join()
        w.process.close()
        self.workers.remove(w)
        logger.debug(f"worker {w.worker_id} has been removed")
