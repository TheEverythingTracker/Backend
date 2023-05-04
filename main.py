import asyncio
from typing import List

import cv2

import logging
from models import dto
from api import websocket
from config.constants import LOG_LEVEL

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


def start_websocket_server():
    """
    Start a server for sending the tracking data over websocket
    """
    websocket_server = websocket.WebSocketServer()
    logger.info("starting websocket server")
    asyncio.run(websocket_server.run())
    return websocket_server


def main():
    websocket_server: websocket.WebSocketServer = start_websocket_server()


if __name__ == '__main__':
    main()
