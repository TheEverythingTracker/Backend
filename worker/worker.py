import multiprocessing

from worker import tracking
from errors import TrackingError


class WorkerProcess:
    def __init__(self, img, bounding_box: tuple, queue: multiprocessing.Queue):
        self.to_worker, self.to_master = multiprocessing.Pipe()
        self.has_quit = multiprocessing.Event()
        self.process = multiprocessing.Process(target=do_work,
                                               args=(img, bounding_box, self.to_worker, queue, self.has_quit))


def do_work(img, bounding_box: tuple, to_worker: multiprocessing.Pipe, queue: multiprocessing.Queue,
            has_quit: multiprocessing.Event):
    tracker = tracking.Tracker(img, bounding_box, to_worker, queue)
    try:
        tracker.run_tracking_loop()
    except (TrackingError, IOError) as e:
        print(e)
        has_quit.set()
        exit(1)
# TODO: raise process deletion from process array
