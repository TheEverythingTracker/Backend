import logging
import time
from uuid import UUID

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import connection_manager
from config.constants import LOG_LEVEL

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

app: FastAPI = FastAPI(title="everythingTracker")


@app.websocket("/{session_id}")
async def connect_websocket(websocket: WebSocket, session_id: UUID):
    await connection_manager.connect(session_id, websocket)
    logger.info(f"Session '{session_id}' opened")

    try:
        time.sleep(1)
        await websocket.send_text("Hello World")
    except WebSocketDisconnect:
        connection_manager.remove_connection(session_id)
        logger.info(f"Session '{session_id}' closed")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
