import asyncio
import multiprocessing
import threading

import cv2
import websocket

from worker import worker

VIDEO_SOURCE = '.resources/race_car.mp4'


def show_debug_output(img, bounding_box):
    """
    For debugging purposes: Show the video with tracking info
    :param img: current frame
    :param bounding_box: bounding box info
    """
    draw_box(img, bounding_box)
    cv2.imshow("Tracking", img)
    if cv2.waitKey(1) & 0xff == ord('q'):
        print("User exit")
        exit(0)


def draw_box(img, bounding_box):
    """
    draw bounding box on next frame
    :param img: frame to print bounding box on
    :param bounding_box: coordinates and dimensions of the bounding box
    """
    x, y, w, h = int(bounding_box[0]), int(bounding_box[1]), int(bounding_box[2]), int(bounding_box[3])
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)
    cv2.putText(img, "Tracking", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


async def main(debug):
    """
    Main entry point for running the tracking loop
    :param debug: enable debug video output
    """
    # todo: can we use some asyncio magic here? --> asyncio is not supposed to be used together with threading
    ws_thread = threading.Thread(target=websocket.start_websocket_server)
    ws_thread.start()

    num_cores = multiprocessing.cpu_count()
    print(f"{num_cores} cores available")

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    success, img = cap.read()
    bounding_box = cv2.selectROI("Tracking", img, False)

    # conn1 to receive data and conn2 to send data
    conn1, conn2 = multiprocessing.Pipe()
    queue = multiprocessing.Queue()

    worker_process = multiprocessing.Process(target=worker.do_work, args=(img, bounding_box, conn1, queue))
    worker_process.start()

    while True:
        success, img = cap.read()  # todo: errorhandling
        conn2.send(img)
        bounding_box = queue.get()
        # todo: build proper json from bounding box, or multiple bounding boxes in the future
        websocket.bounding_box_queue.put(str(bounding_box))
        if debug:
            show_debug_output(img, bounding_box)


if __name__ == '__main__':
    asyncio.run(main(debug=True))
