import cv2

from errors import TrackingError


class Tracker:

    def __init__(self, img, bounding_box):
        """
        initialize object tracker by object selection in first frame
        :param cap: video handle
        :return: created tracker instance
        """
        # TODO: decide on tracker
        tracker = cv2.TrackerMIL_create()
        tracker.init(img, bounding_box)
        self.tracker = tracker

    def update_tracking(self, img):
        success, bounding_box = self.tracker.update(img)
        if success:
            return bounding_box
        else:
            raise TrackingError('Tracking failed')
