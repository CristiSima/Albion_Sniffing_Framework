from event import app
from flask import Blueprint, render_template

from streams import PlayerInfoResponse
from event import send_event_gen, socketio, register_on_event_gen
from pprint import pprint

send_hello_world = send_event_gen("hello_world")
register_on_subscribe = register_on_event_gen("subscribe")

player_name = None

@PlayerInfoResponse.add_hook
def print_player_name(target):
    pprint(target)
    print(target[-1]["player_name"])


@PlayerInfoResponse.add_hook
def hello_world(target):
    send_hello_world((target[-1]["player_name"],))

@PlayerInfoResponse.add_hook
def save_player_name(target):
    global player_name
    player_name = target[-1]["player_name"]

@register_on_subscribe
def on_subscribe(triggering_event, subscribed_to):
    print(f"Subscribe {subscribed_to}|{player_name=}")
    if player_name:

        send_hello_world(player_name)

extension_name = "hello_world"

bp = Blueprint(extension_name, extension_name,
    static_folder=f"extensions/{extension_name}/static",
    template_folder=f"extensions/{extension_name}/templates"
)

@bp.get("/")
def main_page():
    return render_template("hello_world.j2.html")

app.register_blueprint(bp, url_prefix=f"/{extension_name}")