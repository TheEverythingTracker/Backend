import multiprocessing

from worker import tracking
from errors import TrackingError


class WorkerProcess:
    def __init__(self, img, bounding_box: tuple, queue: multiprocessing.Queue):
        self.receiver, self.sender = multiprocessing.Pipe()
        self.has_quit = multiprocessing.Event()
        self.process = multiprocessing.Process(target=do_work,
                                               args=(img, bounding_box, self.receiver, queue, self.has_quit))
        self.process.start()


def do_work(img, bounding_box: tuple, receiver: multiprocessing.Pipe, queue: multiprocessing.Queue,
            has_quit: multiprocessing.Event):
    tracker = tracking.Tracker(img, bounding_box, receiver, queue)
    try:
        tracker.run_tracking_loop()
    except (TrackingError, IOError) as e:
        print(e)
        has_quit.set()
        exit(1)
# TODO: raise process deletion from process array
