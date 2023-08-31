from logging import INFO, DEBUG

LOG_LEVEL = DEBUG
# LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
LOG_FORMAT = '%(levelname)s [%(name)s]:     %(message)s'
VIDEO_SOURCE = '.resources/race_car.mp4'
QUEUE_SIZE = 10
CONSUMER_QUEUE_TIMEOUT = 1
SENDER_QUEUE_TIMEOUT = 4
