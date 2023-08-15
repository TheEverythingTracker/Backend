import logging
from uuid import UUID

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import connection_manager
from business.session import Session
from config.constants import LOG_LEVEL, LOG_FORMAT
from models.errors import DuplicateSessionError
from models.websocket_status_codes import WebsocketStatusCode

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

app: FastAPI = FastAPI(title="TheEverythingTracker")


@app.websocket("/websocket/{session_id}")
async def connect_websocket(websocket: WebSocket, session_id: UUID):
    try:
        await connection_manager.connect(session_id, websocket)
    except DuplicateSessionError as e:
        logger.error(e)
        await websocket.close(code=WebsocketStatusCode.PROTOCOL_ERROR, reason=str(e))
        logger.info(f"Session '{session_id}' rejected")
        return

    try:
        logger.info(f"Session '{session_id}' opened")
        session = Session(session_id, websocket)
        await session.consume_websocket_events()
    except WebSocketDisconnect as e:
        logger.warning(f"WebsocketDisconnect with Reason: {e}")
    finally:
        connection_manager.remove_connection(session_id)
        del session
        logger.info(f"Session '{session_id}' closed")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
