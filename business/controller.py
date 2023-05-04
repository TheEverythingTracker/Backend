import logging
import multiprocessing
import queue
from typing import List

import cv2

from business.debug import show_debug_output
from business.worker.worker import WorkerProcess
from config.constants import LOG_LEVEL, VIDEO_SOURCE
from models import dto
from models.errors import OutOfResourcesError

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def run_control_loop(debug: bool, bounding_boxes_to_websocket_queue: multiprocessing.Queue):
    """
    Main entry point for running the tracking loop
    :param bounding_boxes_to_websocket_queue: queue to send bounding boxes to
    :param debug: enable debug video output
    """
    num_cores: int = multiprocessing.cpu_count()
    logger.debug(f"{num_cores} cores available")

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    success, img = cap.read()  # todo: img is of type numpy.ndarray
    bounding_box: tuple = cv2.selectROI("Tracking", img, False)

    bounding_boxes_from_workers_queue: multiprocessing.Queue = multiprocessing.Queue()

    workers: List[WorkerProcess] = []
    if len(workers) <= num_cores:
        worker_process: WorkerProcess = WorkerProcess(img, bounding_box, bounding_boxes_from_workers_queue,
                                                      len(workers))
        workers.append(worker_process)
        logger.info(f"worker {len(workers)} started")
    else:
        logger.warning("not enough cpu cores")
        raise OutOfResourcesError("not enough cpu cores")

    # todo: is there a better way to get frame numbers?
    frame_number: int = 0
    while workers:
        success, img = cap.read()  # todo: errorhandling
        frame_number += 1
        tracking_event: dto.UpdateTrackingEvent = dto.UpdateTrackingEvent(event_type=dto.EventType.UPDATE_TRACKING,
                                                                          frame=frame_number, bounding_boxes=[])
        # todo: this loop will block until all workers have processed the current frame --> might be a performance bottleneck
        for w in workers.copy():
            if w.has_quit.is_set():
                w.process.join()
                logger.debug(f"worker {w.worker_id} has been removed")
                workers.remove(w)
            else:
                w.sender.send(img)
            try:
                bounding_box: dto.BoundingBox = bounding_boxes_from_workers_queue.get(block=False)
                # todo: dont't put empty bounding boxes into queue and make it asynchronous
                tracking_event.bounding_boxes.append(bounding_box)
            except queue.Empty:
                logger.debug("empty queue")
        logger.debug(tracking_event.bounding_boxes)
        bounding_boxes_to_websocket_queue.put(tracking_event)
        try:
            if debug:
                show_debug_output(img, tracking_event.bounding_boxes)
        except Exception:
            logger.debug("Debug Output failed")

    # Cleanup
    cv2.destroyWindow("Tracking")
    cap.release()
    logger.info("Goodbye!")
