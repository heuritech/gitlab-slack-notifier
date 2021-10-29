from slack import WebClient

from gitlabnotifier.constants import FLASK_ENV, SLACK_API_TOKEN

slack_client = WebClient(token=SLACK_API_TOKEN) if SLACK_API_TOKEN is not None else None
# during unit tests, `SLACK_API_TOKEN` is None


def get_email_to_slack_name():
    email_to_slack_name = {}
    if slack_client is None:
        raise ValueError("You must specify `SLACK_API_TOKEN` to access the Slack API.")
    res = slack_client.users_list()
    members = res['members']
    for member in members:
        res = slack_client.users_profile_get(user=member['id'])
        email = res['profile'].get('email')
        if email:
            email_to_slack_name[email] = '@' + member['name']
    return email_to_slack_name


if FLASK_ENV == 'development' or slack_client is None:
    # Hard-coded names for testing
    EMAIL_TO_SLACK_NAME = {
        "test@mycompany.com": "@test",
    }
else:
    EMAIL_TO_SLACK_NAME = get_email_to_slack_name()


def slack_message(message, channel):
    return slack_client.chat_postMessage(
        channel=channel, username='gitlabnotifier', icon_emoji=':gitlab:', **message
    )
