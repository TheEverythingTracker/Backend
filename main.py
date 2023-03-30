import multiprocessing

import cv2
import websocket

from worker import worker

VIDEO_SOURCE = '.resources/race_car.mp4'


def show_debug_output(img, bounding_box, fps):
    """
    For debugging purposes: Show the video with tracking info
    :param img: current frame
    :param bounding_box: bounding box info
    :param fps: framerate
    """
    draw_box(img, bounding_box)
    cv2.putText(img, str(int(fps)), (75, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
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


def main(debug):
    """
    Main entry point for running the tracking loop
    :param debug: enable debug video output
    """
    websocket.start_websocket_server()

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    success, img = cap.read()
    bounding_box = cv2.selectROI("Tracking", img, False)

    # conn1 to receive data and conn2 to send data
    conn1, conn2 = multiprocessing.Pipe()
    queue = multiprocessing.Queue()

    worker_process = multiprocessing.Process(target=worker.do_work, args=(img, bounding_box, conn1, queue))
    worker_process.start()

    queue.get()

    if debug:
        show_debug_output(img, bounding_box)


if __name__ == '__main__':
    main(debug=True)
