import logging
import multiprocessing

from config.constants import LOG_LEVEL
from business.worker import tracking
from models.errors import TrackingError

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class WorkerProcess:
    def __init__(self, img, bounding_box: tuple, queue: multiprocessing.Queue, worker_id: int):
        self.worker_id = worker_id
        self.receiver, self.sender = multiprocessing.Pipe()
        self.has_quit = multiprocessing.Event()
        self.process = multiprocessing.Process(target=do_work,
                                               args=(img, bounding_box, self.receiver, queue, self.has_quit, self.worker_id))
        self.process.start()


def do_work(img, bounding_box: tuple, receiver: multiprocessing.Pipe, queue: multiprocessing.Queue,
            has_quit: multiprocessing.Event, worker_id: int):
    tracker = tracking.Tracker(img, bounding_box, receiver, queue)
    try:
        tracker.run_tracking_loop(worker_id)
    except (TrackingError, IOError) as e:
        logger.warning(e)
        has_quit.set()
        exit(1)
# TODO: raise process deletion from process array
