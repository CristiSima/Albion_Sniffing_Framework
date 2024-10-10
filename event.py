from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
from threading import Thread
from typing import List, Dict, Callable
from queue import Queue
from time import sleep
from functools import partial

__all__ = [
    "send_event",
    "send_event_gen",
    "register_on_event",
    "register_on_event_gen",
]

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.event
def connect(arg):
    do_on_event("connect")
    print("New Client ", request.sid)

@socketio.event
def disconnect():
    do_on_event("disconnect")
    print('Disconnected ', request.sid)

@socketio.event
def subscribe(event_name):
    print("subscribed ", event_name)
    join_room(event_name)

    do_on_event("subscribe", subscrive_to=event_name)

@socketio.event
def unsubscribe(event_name):
    print("unsubscribe ", event_name)
    do_on_event("unsubscribe")
    leave_room(event_name, unsubscribe_from=event_name)


@socketio.event
def echo(data):
    emit("echo", "data", to=request.sid)


event_queue = Queue()
queue_consumer = False

def later_loop():
    global queue_consumer
    queue_consumer = True

    print("later_loop started")
    while True:
        event_name, data = event_queue.get()
        socketio.emit(event_name, data, to=event_name)


def send_event(event_name: str, data):
    '''
    fake sender, adds to queue
    '''
    if queue_consumer:
        event_queue.put_nowait((event_name, data))

def send_event_gen(event_name: str):
    return partial(send_event, event_name)


event_callbacks: Dict[str, List[Callable[[str,], None]]] = {}


def register_on_event(triggering_event: str, callback_function: Callable[[str, ...], None]):
    if triggering_event not in event_callbacks:
        event_callbacks[triggering_event] = []

    event_callbacks[triggering_event].append(callback_function)

def register_on_event_gen(triggering_event: str):
    return partial(register_on_event, triggering_event)


def do_on_event(triggering_event: str, *args, **kwargs):
    for callback_function in event_callbacks.get(triggering_event, []):
        callback_function(triggering_event, *args, **kwargs)


@app.route("/site-map")
def site_map():
    return repr(app.url_map)


t = Thread(target=socketio.run, args=[app,], kwargs={"port":5055}, daemon=True)
loop_task = Thread(target=later_loop, daemon=True)

def start():
    t.start()
    loop_task.start()


if __name__ == '__main__':
    start()
    sleep(10)

    print("DONE")
