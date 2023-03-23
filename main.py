
import cv2


def draw_box(img, bounding_box):
    x, y, w, h = int(bounding_box[0]), int(bounding_box[1]), int(bounding_box[2]), int(bounding_box[3])
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)
    cv2.putText(img, "Tracking", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


def init_tracker(cap):
    # tracker = cv2.TrackerMIL_create()
    # decide on tracker
    tracker = cv2.TrackerMIL_create()
    success, img = cap.read()
    bounding_box = cv2.selectROI("Tracking", img, False)
    tracker.init(img, bounding_box)
    return tracker


def main():
    cap = cv2.VideoCapture('.resources/race_car.mp4')
    tracker = init_tracker(cap)

    while True:
        timer = cv2.getTickCount()
        success, img = cap.read()

        success, bounding_box = tracker.update(img)

        if success:
            draw_box(img, bounding_box)
        else:
            cv2.putText(img, "Lost Tracker", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
        cv2.putText(img, str(int(fps)), (75, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.imshow("Tracking", img)

        if cv2.waitKey(1) & 0xff == ord('q'):
            break


if __name__ == '__main__':
    main()
