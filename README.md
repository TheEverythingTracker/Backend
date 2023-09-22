# Backend

## todo: Explain Poetry Basics
[Poetry Docs](https://python-poetry.org/docs/cli/)

# Mulitprocessing
* 1 main process for management 
  * Managing Websocket
  * Starting/stopping Processes for object tracking
  * getting data from worker processes and passing them to the websocket
* n Worker Processes for object tracking

## Why Mulitprocessing instead of Multithreading?
Due to the global Interpreter Lock (GIL) in the case of Multithreading there would still only be executed one thread at a time 

-> No Performance benefit for tracking

## Discuss
* 