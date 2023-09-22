from enum import Enum


# Websocket Status Codes: https://datatracker.ietf.org/doc/html/rfc6455#section-7.4.1
class WebsocketStatusCode(int, Enum):
    NORMAL_CLOSE = 1000
    SERVER_SHUTDOWN = 1001
    PROTOCOL_ERROR = 1002
    WRONG_DATA_TYPE = 1003