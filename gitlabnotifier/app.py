import json
import logging

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import Forbidden

from gitlabnotifier.constants import (DEV_CHANEL, FLASK_ENV, GLOBAL_CHANEL, X_GITLAB_TOKEN)
from gitlabnotifier.process_gitlab_notif import \
    get_messages_and_emails_from_event
from gitlabnotifier.slack_api import EMAIL_TO_SLACK_NAME, slack_message

app = Flask(__name__)


def process_notification(event):
    message, user_emails = get_messages_and_emails_from_event(event)
    if FLASK_ENV == 'development':
        message['attachments'] = message.get("attachments", []) + [{"text": json.dumps(event)}]
        slack_message(message, DEV_CHANEL)
    if not message or not user_emails:
        logging.warn(
            f"Event {event['object_kind']} {event.get('object_attributes', '')}"
            " did not produce notifications."
        )

    user_emails_not_matched = set()
    print(f"user_emails = {user_emails}")
    for user_email in user_emails:
        slack_username = EMAIL_TO_SLACK_NAME.get(user_email)
        if not slack_username:
            user_emails_not_matched.add(user_email)
        else:
            res_slack_user = slack_message(message, slack_username)
            print(f"Tried sending to {slack_username}, response: {res_slack_user}")
            if res_slack_user['ok']:
                yield message
            else:
                user_emails_not_matched.add(user_email)

    if user_emails_not_matched:
        message['text'] += f" (user emails {user_emails_not_matched} " \
                           f"do not match a slack username !)"
        res_slack_global = slack_message(message, GLOBAL_CHANEL)
        if not res_slack_global['ok']:
            print("Error sending notif to slack: %s" % json.dumps(res_slack_global))
            yield f"Failed to send slack message to {user_emails_not_matched} or {GLOBAL_CHANEL}"
        yield message


@app.before_request
def check_token():
    header_token = request.headers.get('x-gitlab-token')
    if X_GITLAB_TOKEN is not None and header_token != X_GITLAB_TOKEN:
        raise Forbidden('Missing or invalid x-gitlab-token header.')


@app.route("/", methods=["POST"])
def post_route():
    event = request.json
    if FLASK_ENV == 'development':
        print(json.dumps(event, indent=4))
    msgs = list(process_notification(event))
    if msgs:
        print(msgs)
    return "Event processed."


@app.route("/")
def get_route():
    return jsonify({"message": "dummy"})
