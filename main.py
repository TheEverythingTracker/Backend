import logging
import uvicorn
from fastapi import FastAPI

from config.constants import LOG_LEVEL

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

app: FastAPI = FastAPI(title="everythingTracker")


@app.get("/health")
def get_health():
    return "I'm ok"


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
