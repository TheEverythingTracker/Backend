# TheEverytingTracker Backend

FastAPI Backend for playing video and interactively tracking displayed objects.

## Run

#### Run Frontend:

```
docker run -it -p 8080:80 --name 'TheEverythingTracker_Frontend' ghcr.io/theeverythingtracker/frontend:main
```

#### Run Backend:

```
docker run -p 8000:8000 --name 'TheEverythingTracker_Backend' ghcr.io/theeverythingtracker/backend:main
```

#### Connect to Frontend:

[TheEverythingTracker](http://localhost:8080)

## todo: Explain Poetry Basics

[Poetry Docs](https://python-poetry.org/docs/cli/)

# Mulitprocessing

* 1 main process for management
    * Managing Websocket
    * Starting/stopping Processes for object tracking
    * getting data from worker processes and passing them to the websocket
* n Worker Processes for object tracking

## Why Mulitprocessing instead of Multithreading?

Due to the global Interpreter Lock (GIL) in the case of Multithreading there would still only be executed one thread at
a time

-> No Performance benefit for tracking

## Discuss

* 