FROM python:3.11-slim

LABEL org.opencontainers.image.description="TheEverythingTracker/Backend: Reads a video-stream and outputs tracking data for TheEverythingTracker/Frontend."

RUN useradd -u 8877 containeruser

WORKDIR /code
COPY pyproject.toml /code

# Install cv2 dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip3 install --no-cache-dir poetry
# do not create virtual env since we already are in a container
RUN poetry config virtualenvs.create false

# install
RUN poetry install --no-dev

USER containeruser
# changes often so put as close to the end as possible since the rest can be cached by docker
COPY ./app /code/app

WORKDIR /code/app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
