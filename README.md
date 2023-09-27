[![Build Docker-Image](https://github.com/TheEverythingTracker/Backend/actions/workflows/docker-publish.yml/badge.svg?branch=main)](https://github.com/TheEverythingTracker/Backend/actions/workflows/docker-publish.yml)

# TheEverytingTracker Backend

Backend for playing video and interactively tracking displayed objects.

## How to run

### Docker

#### Prerequisites:

You need Docker installed on your machine. See [Docker Docs](https://docs.docker.com/engine/install/) for installation
instructions.

#### Run the Frontend Docker-Container:

```shell
docker run -it -p 8080:80 --name 'TheEverythingTracker_Frontend' ghcr.io/theeverythingtracker/frontend:main
```

#### Run the Backend Docker-Container:

```shell
docker run -p 8000:8000 --name 'TheEverythingTracker_Backend' ghcr.io/theeverythingtracker/backend:main
```

#### Connect to the Frontend:

[TheEverythingTracker](http://localhost:8080)

### Without Docker:

1. Clone this repository, install the dependencies (maybe use Poetry, see the ["Set up"](#set-up) section in this
   document) and run ```python ./app/main.py```
2. Learn how to run the Frontend here: [TheEverytingTracker/Frontend](https://github.com/TheEverythingTracker/Frontend)

## Technology Overview

This application uses the following core dependencies:

- [FastAPI](https://fastapi.tiangolo.com/) as Framework for managing Websockets
- [OpenCV](https://opencv.org/) for tracking and video related workloads
- [uvicorn](https://www.uvicorn.org/) as ASGI web server for serving the application

## Contributing

### Guidelines

- Every feature should be described in an issue and implemented in a branch linked to that issue

### Set up

1. If you don't have already: Install [Python](https://www.python.org/)
2. This project uses Poetry for dependency-management. If you don't have it: Set up Python Poetry by following
   these [Instructions](https://python-poetry.org/docs/).
3. Clone the project
4. Create a virtual environment and install dependencies into it with ```poetry install``` while in the project
   directory
5. Run ```python ./app/main.py```

### Build a new Docker Image

Whenever new Changes are pushed to the "main" branch, a new Docker image will be built
by this [GitHub Actions Pipeline](https://github.com/TheEverythingTracker/Backend/actions/workflows/docker-publish.yml).
You can find the latest Docker image [here](https://github.com/orgs/TheEverythingTracker/packages?repo_name=Backend).