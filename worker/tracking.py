import cv2

from dto import BoundingBox
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

    def run_tracking_loop(self, worker_id: int):
        """
        Run the tracking loop and fill the queue with tracking data
        :return:
        """
        while True:
            img = self.receiver.recv()
            bounding_box: tuple = self.update_tracking(img)
            self.queue.put(BoundingBox(id=worker_id, x=bounding_box[0], y=bounding_box[1], width=bounding_box[2],
                                       height=bounding_box[3]))

# Frames droppen um den neuen wieder zu bekommen
# numdropped = 0
# while pipe.poll:
#   pipe.receive
#   numdropped++
# return numdropped
