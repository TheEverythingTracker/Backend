import cv2

from errors import TrackingError


class Tracker:

    def __init__(self, img, bounding_box, receiver, queue):
        """
        initialize object tracker by object selection in first frame
        :param cap: video handle
        :return: created tracker instance
        """
        # TODO: decide on tracker
        tracker = cv2.TrackerMIL_create()
        tracker.init(img, bounding_box)
        self.receiver = receiver
        self.queue = queue
        self.tracker = tracker

    def update_tracking(self, img):
        success, bounding_box = self.tracker.update(img)
        if success:
            return bounding_box
        else:
            raise TrackingError('Tracking failed')

    def run_tracking_loop(self):
        """
        Run the tracking loop and fill the queue with tracking data
        :param cap: video source cv2 capture
        :param tracker: tracker object to use for tracking
        :param debug: show video for debugging
        :return:
        """
        while True:
            img = self.receiver.recv()
            bounding_box = self.update_tracking(img)

            # todo better json representation of bounding box (or multiple ones)
            self.queue.put(bounding_box)


# Frames droppen um den neuen wieder zu bekommen
# numdropped = 0
# while pipe.poll:
#   pipe.receive
#   numdropped++
# return numdropped