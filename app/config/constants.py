from logging import INFO, DEBUG

LOG_LEVEL = DEBUG
# LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
LOG_FORMAT = '%(levelname)s [%(name)s]:     %(message)s'
VIDEO_SOURCE = '.resources/race_car.mp4'
QUEUE_SIZE = 10
PRODUCER_THREAD_SEEMS_DEAD_TIMEOUT = 5
NO_UPDATES_TO_SEND_TIMEOUT = 1
