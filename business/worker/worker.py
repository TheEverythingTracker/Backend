import logging
import multiprocessing

from business.worker import tracking
from config.constants import LOG_LEVEL
from models.errors import TrackingError

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


class WorkerProcess:
    worker_id: int
    receiver = None
    sender = None
    should_exit: multiprocessing.Event = None
    process: multiprocessing.Process

    def __init__(self, img, bounding_box: tuple, queue: multiprocessing.Queue, worker_id: int):
        self.worker_id = worker_id
        self.receiver, self.sender = multiprocessing.Pipe()
        self.should_exit = multiprocessing.Event()
        self.process = multiprocessing.Process(target=do_work,
                                               args=(
                                                   img, bounding_box, self.receiver, queue, self.should_exit,
                                                   self.worker_id))
        self.process.start()


def do_work(img, bounding_box: tuple, receiver: multiprocessing.Pipe, queue: multiprocessing.Queue,
            should_exit: multiprocessing.Event, worker_id: int):
    tracker = tracking.Tracker(img, bounding_box, receiver, queue)
    try:
        tracker.run_tracking_loop(worker_id, should_exit)
    except (TrackingError, IOError) as e:
        logger.warning(e)
        should_exit.set()
        exit(1)
    finally:
        logger.info(f"worker {worker_id} has finished execution")
        exit(0)
# TODO: raise process deletion from process array
