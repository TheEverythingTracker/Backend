import asyncio
import multiprocessing
import queue
from typing import List

import cv2

import logging
import dto
import websocket
from constants import LOG_LEVEL
from errors import OutOfResourcesError
from worker.worker import WorkerProcess

VIDEO_SOURCE = '.resources/race_car.mp4'

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def show_debug_output(img, bounding_boxes: List[dto.BoundingBox]):
    """
    For debugging purposes: Show the video with tracking info
    :param img: current frame
    :param bounding_boxes: List of bounding boxes
    """
    cv2.putText(img, "Tracking", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    for bounding_box in bounding_boxes:
        draw_box(img, bounding_box)
    cv2.imshow("Tracking", img)
    if cv2.waitKey(1) & 0xff == ord('q'):
        logger.debug("User exit")
        exit(0)


def draw_box(img, bounding_box: dto.BoundingBox):
    """
    draw bounding box on next frame
    :param img: frame to draw bounding box on
    :param bounding_box: coordinates and dimensions of the bounding box
    """
    x, y, w, h = int(bounding_box.x), int(bounding_box.y), int(bounding_box.width), int(bounding_box.height)
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)


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
        worker_process: WorkerProcess = WorkerProcess(img, bounding_box, bounding_boxes_from_workers_queue, len(workers))
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


def start_websocket_server():
    """
    Start a server for sending the tracking data over websocket
    """
    websocket_server = websocket.WebSocketServer()
    logger.info("starting websocket server")
    asyncio.run(websocket_server.run())
    return websocket_server


def main():
    websocket_server: websocket.WebSocketServer = start_websocket_server()


if __name__ == '__main__':
    main()
