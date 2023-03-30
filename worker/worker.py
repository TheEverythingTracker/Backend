import tracking
from errors import TrackingError


def do_work(img, bounding_box, conn2, queue):
    tracker = tracking.Tracker(img, bounding_box, conn2, queue)
    try:
        tracker.run_tracking_loop()
    except (TrackingError, IOError) as e:
        print(e)
        return
