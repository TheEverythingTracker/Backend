import logging
from typing import List

import cv2

from app.config.constants import LOG_LEVEL
from app.models import dto

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def show_debug_output(img, bounding_boxes: List[dto.BoundingBox]):
    """
    For debugging purposes: Show the video with tracking info
    :param img: current frame
    :param bounding_boxes: List of bounding boxes
    """
    cv2.putText(img, "Tracking", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    for bounding_box in bounding_boxes:
        draw_box(img, bounding_box)
    cv2.imshow("Tracking", img)
    if cv2.waitKey(1) & 0xff == ord('q'):
        logger.debug("User exit")
        exit(0)


def draw_box(img, bounding_box: dto.BoundingBox):
    """
    draw bounding box on next frame
    :param img: frame to draw bounding box on
    :param bounding_box: coordinates and dimensions of the bounding box
    """
    x, y, w, h = int(bounding_box.x), int(bounding_box.y), int(bounding_box.width), int(bounding_box.height)
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)
