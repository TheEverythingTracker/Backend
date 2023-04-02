import multiprocessing
import queue
import random
import threading
from typing import List

import cv2

import websocket
from errors import OutOfResourcesError
from worker.worker import WorkerProcess

VIDEO_SOURCE = '.resources/race_car.mp4'


def show_debug_output(img, bounding_boxes: List[tuple]):
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
        print("User exit")
        exit(0)


def draw_box(img, bounding_box: tuple):
    """
    draw bounding box on next frame
    :param img: frame to print bounding box on
    :param bounding_box: coordinates and dimensions of the bounding box
    """
    x, y, w, h = int(bounding_box[0]), int(bounding_box[1]), int(bounding_box[2]), int(bounding_box[3])
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)


def main(debug: bool):
    """
    Main entry point for running the tracking loop
    :param debug: enable debug video output
    """
    # todo: can we use some asyncio magic here? --> asyncio is not supposed to be used together with threading
    ws_thread = threading.Thread(target=websocket.start_websocket_server)
    ws_thread.start()

    num_cores: int = multiprocessing.cpu_count()
    print(f"{num_cores} cores available")

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    success, img = cap.read()  # todo: img is of type numpy.ndarray
    bounding_box = cv2.selectROI("Tracking", img, False)

    bounding_box_queue = multiprocessing.Queue()

    workers = []
    if len(workers) <= num_cores:
        worker_process = WorkerProcess(img, bounding_box, bounding_box_queue)
        workers.append(worker_process)
        print(f"worker {len(workers)} started")
    else:
        raise OutOfResourcesError("Not enough cpu cores")

    while workers:
        success, img = cap.read()  # todo: errorhandling
        bounding_boxes = []
        # todo: this loop will block until all workers have processed the current frame --> might be a performance bottleneck
        for w in workers.copy():
            if w.has_quit.is_set():
                w.process.join()
                workers.remove(w)
            else:
                w.sender.send(img)
            try:
                bounding_box = bounding_box_queue.get(block=False)
                bounding_boxes.append(bounding_box)
            except queue.Empty:
                # todo: dont't put empty bounding boxes into queue
                print("empty queue")
        print(bounding_boxes)
        # todo: build proper json from bounding box, or multiple bounding boxes in the future
        websocket.bounding_box_queue.put(str(bounding_boxes))
        try:
            if debug:
                show_debug_output(img, bounding_boxes)
        except Exception:
            print("Debug Output failed")

    # Cleanup
    cv2.destroyWindow("Tracking")
    print("Goodbye!")


if __name__ == '__main__':
    main(debug=True)
