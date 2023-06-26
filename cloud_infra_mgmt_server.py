import os
from pathlib import Path
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify
from slack_bolt import App, Say
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
from apscheduler.schedulers.background import BackgroundScheduler
import time
import json
from cluster_management import ClusterMgmt, ClusterDbMgmt

# Initialize Flask app and Slack app
app = Flask(__name__)

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
slack_app = App(
    token=os.environ['BOT_TOKEN'],
    signing_secret=os.environ['SIGNING_SECRET']
)

client = WebClient(token=os.environ.get("BOT_TOKEN"))

global obj_cluster


# Route for handling slash command requests
@app.route("/slack/command", methods=["POST", "GET"])
def command():
    message = cmd_text = None
    load_dotenv(dotenv_path=env_path)
    # Parse request body data
    data = request.form
    print("serving {} cluster".format(data["command"]))
    # Call the appropriate function based on the slash command
    if data["command"] == "/create_cluster":
        cmd_text = data.get('text')
        if cmd_text:
            message = obj_cluster.initiate_cluster_creation(data['user_id'],
                                                            cmd_text)
        # message = get_joke()
    elif data["command"] == "/delete_cluster":
        cmd_text = data.get('text')
        if cmd_text:
            message = obj_cluster.delete_cluster(data['user_id'],
                                                 cmd_text)
    elif data["command"] == "/clusters":
        message = obj_cluster.get_clusters_by_user(data['user_id'])
    else:
        message = f"Invalid command: {data['command']}"

    if not message:
        message = "command parameters are not provided"
    # Return response to Slack
    return jsonify({"text": str(message)})


@app.route("/update", methods=["PUT", "POST"])
def update_cluster_info():
    print("in update cluster info: {}".format(request))
    json_data = request.get_json()
    user_name = json_data.pop('user_id')
    obj_cluster.update_cluster_attribute(user_name, json_data)
    msg = None
    if json_data.get('status') == 'running':
        msg = 'cluster:{} got created successfully and in running state.' \
              ' Run command: /clusters to know details to login'. \
            format(json_data.get('name'))
    elif json_data.get('status') == 'delete_success':
        msg = "Cluster {} deleted successfully".format(json_data.get('name'))
    elif json_data.get('status') == 'delete_failed':
        msg = "Cluster {} failed to delete".format(json_data.get('name'))
    else:
        msg = 'cluster: {} creation failed'
    client.chat_postMessage(channel=config_json.get('SLACK_CHANNEL'),
                            text=msg)

    return "success", 201


@app.route("/slacky/events", methods=["POST"])
def slack_events():
    """ Declaring the route where slack will post a request """
    return handler.handle(request)


@slack_app.message("hello")
def greetings(payload: dict, say: Say):
    """ This will check all the message and pass only those which has 'hello slacky' in it """
    user = payload.get("user")
    say(f"Hi <@{user}>")


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


# Function for getting a random joke from the icanhazdadjoke API
def get_joke():
    url = "https://icanhazdadjoke.com/"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers, timeout=5)
    joke = response.json()["joke"]
    return joke


# Initialize SlackRequestHandler to handle requests from Slack
handler = SlackRequestHandler(slack_app)


def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


def alert_expiring_clusters():
    exp_duration = config_json['CLUSTER_EXPIRATION_DURATION']*24
    msg = 'Following clusters will be expiring soon: {}'.format(obj_cluster.get_expiring_clusters(exp_duration))
    client.chat_postMessage(channel=config_json.get('SLACK_CHANNEL'),
                            text=msg)


if __name__ == "__main__":
    global obj_cluster
    config_json = None
    with open('config.json') as fp:
        config_json = json.load(fp)

    obj_cluster = ClusterMgmt()
    obj_cluster.set_config_data(config_json)
    # obj_cluster.initiate_cluster_creation('manish singh',
    #                                       'name:cluster_name, version:4.9, type:AWS_ROSA, ')
    # data = obj_cluster.get_clusters_by_user('manish singh')
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=alert_expiring_clusters, trigger="interval",
                      seconds=config_json['CLUSTER_POLL_INTERVAL'])
    scheduler.start()
    # Start the Flask app on port 5000
    app.run(port=5000, debug=True)
