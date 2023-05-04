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
    workers: List[WorkerProcess]
    bounding_boxes_to_websocket_queue: multiprocessing.Queue
    bounding_boxes_from_workers_queue: multiprocessing.Queue
    controller_thread: threading.Thread

    def __init__(self, video_source: str, bounding_boxes_to_websocket_queue: multiprocessing.Queue):
        self.num_cores = multiprocessing.cpu_count()
        self.video_source = video_source
        self.workers = []
        self.bounding_boxes_to_websocket_queue = bounding_boxes_to_websocket_queue
        self.bounding_boxes_from_workers_queue = multiprocessing.Queue()

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

    def start_thread(self):
        # todo: how to stop the thread?
        self.controller_thread = threading.Thread(target=self.__run)
        self.controller_thread.start()

    def __run(self):
        video_capture: cv2.VideoCapture = cv2.VideoCapture(self.video_source)
        # todo: is there a better way to get frame numbers?
        frame_number: int = 0
        while self.workers:
            success, img = video_capture.read()  # todo: errorhandling
            frame_number += 1
            tracking_event: dto.UpdateTrackingEvent = dto.UpdateTrackingEvent(event_type=dto.EventType.UPDATE_TRACKING,
                                                                              frame=frame_number, bounding_boxes=[])
            # todo: this loop will block until all workers have processed the current frame --> might be a performance bottleneck
            for w in self.workers.copy():
                if w.has_quit.is_set():
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
            if not tracking_event.bounding_boxes:
                continue
            self.bounding_boxes_to_websocket_queue.put(tracking_event)
            try:
                show_debug_output(img, tracking_event.bounding_boxes)
            except Exception:
                logger.debug("Debug Output failed")

        # Cleanup
        video_capture.release()
        logger.info("Goodbye!")

    def __remove_worker(self, w: WorkerProcess):
        w.process.join()
        w.process.close()
        logger.debug(f"worker {w.worker_id} has been removed")
        self.workers.remove(w)

# ---------------------- Old implementation for reference: we might need some code from here later -----------------
# def run_control_loop(debug: bool, bounding_boxes_to_websocket_queue: multiprocessing.Queue):
#     """
#     Main entry point for running the tracking loop
#     :param bounding_boxes_to_websocket_queue: queue to send bounding boxes to
#     :param debug: enable debug video output
#     """
#     num_cores: int = multiprocessing.cpu_count()
#     logger.debug(f"{num_cores} cores available")
#
#     cap = cv2.VideoCapture(VIDEO_SOURCE)
#     success, img = cap.read()  # todo: img is of type numpy.ndarray
#     bounding_box: tuple = cv2.selectROI("Tracking", img, False)
#
#     bounding_boxes_from_workers_queue: multiprocessing.Queue = multiprocessing.Queue()
#
#     workers: List[WorkerProcess] = []
#     if len(workers) <= num_cores:
#         worker_process: WorkerProcess = WorkerProcess(img, bounding_box, bounding_boxes_from_workers_queue,
#                                                       len(workers))
#         workers.append(worker_process)
#         logger.info(f"worker {len(workers)} started")
#     else:
#         logger.warning("not enough cpu cores")
#         raise OutOfResourcesError("not enough cpu cores")
#
#     # todo: is there a better way to get frame numbers?
#     frame_number: int = 0
#     while workers:
#         success, img = cap.read()  # todo: errorhandling
#         frame_number += 1
#         tracking_event: dto.UpdateTrackingEvent = dto.UpdateTrackingEvent(event_type=dto.EventType.UPDATE_TRACKING,
#                                                                           frame=frame_number, bounding_boxes=[])
#         # todo: this loop will block until all workers have processed the current frame --> might be a performance bottleneck
#         for w in workers.copy():
#             if w.has_quit.is_set():
#                 w.process.join()
#                 logger.debug(f"worker {w.worker_id} has been removed")
#                 workers.remove(w)
#             else:
#                 w.sender.send(img)
#             try:
#                 bounding_box: dto.BoundingBox = bounding_boxes_from_workers_queue.get(block=False)
#                 # todo: dont't put empty bounding boxes into queue and make it asynchronous
#                 tracking_event.bounding_boxes.append(bounding_box)
#             except queue.Empty:
#                 logger.debug("empty queue")
#         logger.debug(tracking_event.bounding_boxes)
#         bounding_boxes_to_websocket_queue.put(tracking_event)
#         try:
#             if debug:
#                 show_debug_output(img, tracking_event.bounding_boxes)
#         except Exception:
#             logger.debug("Debug Output failed")
#
#     # Cleanup
#     cv2.destroyWindow("Tracking")
#     cap.release()
#     logger.info("Goodbye!")
