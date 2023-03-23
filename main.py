import cv2

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


def init_tracker(cap):
    """
    initialize object tracker by object selection in first frame
    :param cap: video handle
    :return: created tracker instance
    """
    # TODO: decide on tracker
    tracker = cv2.TrackerMIL_create()
    success, img = cap.read()
    bounding_box = cv2.selectROI("Tracking", img, False)
    tracker.init(img, bounding_box)
    return tracker


def calculate_fps(starting_clock_tick, ending_clock_tick):
    """
    calculate framerate of the video playback
    :param starting_clock_tick: cpu clock tick at the beginning of the calculation
    :param ending_clock_tick: cpu clock tick at the end of the calculation
    :return: framerate
    """
    return cv2.getTickFrequency() / (ending_clock_tick - starting_clock_tick)


def main():

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    tracker = init_tracker(cap)

    while True:
        starting_clock_tick = cv2.getTickCount()
        success, img = cap.read()
        success, bounding_box = tracker.update(img)

        if success:
            draw_box(img, bounding_box)
        else:
            cv2.putText(img, "lost tracker", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        ending_clock_tick = cv2.getTickCount()
        fps = calculate_fps(starting_clock_tick, ending_clock_tick)
        cv2.putText(img, str(int(fps)), (75, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.imshow("tracking", img)

        if cv2.waitKey(1) & 0xff == ord('q'):
            break


if __name__ == '__main__':
    main()
