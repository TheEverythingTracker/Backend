"""Not using a class, because we want connection_manager to be a Singleton"""

from uuid import UUID

from fastapi import WebSocket
from models import dto
from models.websocket_status_codes import WebsocketStatusCode
from models.errors import DuplicateSessionError

__active_connections: dict[UUID, WebSocket] = {}


def get_session_count() -> int:
    return len(__active_connections)


async def connect(connection_id: UUID, websocket: WebSocket):
    await websocket.accept()
    if connection_id not in __active_connections:
        __active_connections[connection_id] = websocket
    else:
        await websocket.close(code=WebsocketStatusCode.PROTOCOL_ERROR)
        return DuplicateSessionError(f"Session with ID '{connection_id}' already exists")


def remove_connection(connection_id: UUID):
    """remove but don't close connection"""
    __active_connections.pop(connection_id)


async def close_connection(connection_id: UUID):
    """close and remove connection"""
    await __active_connections.pop(connection_id).close(code=WebsocketStatusCode.NORMAL_CLOSE.value)


async def broadcast_event(event: dto.Event):
    for connection in __active_connections.values():
        await connection.send_json(event)


def get_by_id(connection_id: UUID) -> WebSocket:
    return __active_connections[connection_id]
