import logging
from uuid import UUID

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import connection_manager
from config.constants import LOG_LEVEL
from models.errors import DuplicateSessionError

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

app: FastAPI = FastAPI(title="TheEverythingTracker")


@app.websocket("/websocket/{session_id}")
async def connect_websocket(websocket: WebSocket, session_id: UUID):
    try:
        await connection_manager.connect(session_id, websocket)
        logger.info(f"Session '{session_id}' opened")
        # todo session object anlegen
        await websocket.send_text("Hello World")
        async for message in websocket.iter_text():
            logger.debug(f"{session_id}: {message}")
            if message == "bye":
                await connection_manager.close_connection(session_id)
                break
    except WebSocketDisconnect as e:
        logger.error(e)
        connection_manager.remove_connection(session_id)
        logger.info(f"Session '{session_id}' closed")
    except DuplicateSessionError as e:
        logger.error(e)
        logger.info(f"Session '{session_id}' rejected")
    finally:
        pass
        # todo session object zerstören


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
