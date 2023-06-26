""" Basic operations using Slack_sdk """

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
""" We need to pass the 'Bot User OAuth Token' """
slack_token = os.environ.get('BOT_TOKEN')

# Creating an instance of the Webclient class
client = WebClient(token=slack_token)

try:
    # # Posting a message in #random channel
    # response = client.chat_postMessage(
    #     channel="slack-testing",
    #     text="Bot's first message")


    # Sending a message to a particular user
    # response = client.chat_postEphemeral(
    #     channel="slack-testing",
    #     text="Hello",
    #     user="UManish")

    # Get basic information of the channel where our Bot has access
    response = client.conversations_info(
        channel="slack-testing")

    # Get a list of conversations
    response = client.conversations_list()
    print(response["channels"])

except SlackApiError as e:
    assert e.response["error"]