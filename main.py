import asyncio
import threading

import cv2
import websocket

import tracking
from errors import TrackingError

VIDEO_SOURCE = '.resources/race_car.mp4'


def draw_box(img, bounding_box):
    """
    draw bounding box on next frame
    :param img: frame to print bounding box on
    :param bounding_box: coordinates and dimensions of the bounding box
    """
    x, y, w, h = int(bounding_box[0]), int(bounding_box[1]), int(bounding_box[2]), int(bounding_box[3])
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)
    cv2.putText(img, "Tracking", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


def calculate_fps(starting_clock_tick, ending_clock_tick):
    """
    calculate framerate of the video playback
    :param starting_clock_tick: cpu clock tick at the beginning of the calculation
    :param ending_clock_tick: cpu clock tick at the end of the calculation
    :return: framerate
    """
    return cv2.getTickFrequency() / (ending_clock_tick - starting_clock_tick)


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


async def run_tracking_loop(cap, tracker, debug=False):
    """
    Run the tracking loop and fill the queue with tracking data
    :param cap: video source cv2 capture
    :param tracker: tracker object to use for tracking
    :param debug: show video for debugging
    :return:
    """
    while True:
        starting_clock_tick = cv2.getTickCount()

        success, img = cap.read()
        if not success:
            raise IOError('Could not read frame')
        bounding_box = tracker.update_tracking(img)
        fps = calculate_fps(starting_clock_tick, cv2.getTickCount())
        # todo better json representation of bounding box (or multiple ones)
        websocket.bounding_box_queue.put(str(bounding_box))

        if debug:
            show_debug_output(img, bounding_box, fps)


async def main(debug):
    """
    Main entry point for running the tracking loop
    :param debug: enable debug video output
    """
    ws_thread = threading.Thread(target=websocket.start_websocket_server)
    ws_thread.start()

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    success, img = cap.read()
    bounding_box = cv2.selectROI("Tracking", img, False)
    tracker = tracking.Tracker(img, bounding_box)
    try:
        await run_tracking_loop(cap, tracker, debug)
    except (TrackingError, IOError) as e:
        print(e)
        return


if __name__ == '__main__':
    asyncio.run(main(debug=True))
