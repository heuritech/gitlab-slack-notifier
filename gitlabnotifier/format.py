import re
from typing import Dict

from gitlabnotifier.slack_api import EMAIL_TO_SLACK_NAME


def format_slack_link(link: str, name: str):
    name = format_slack_text(name)
    return f"<{link}|{name}>"


def format_slack_text(text: str):
    """This method is used to remove the Slack special characters from a text that will be sent.
    You can test different formats in this interface: https://app.slack.com/block-kit-builder/T03AWMGU2#%7B%22blocks%22:%5B%7B%22type%22:%22section%22,%22text%22:%7B%22type%22:%22mrkdwn%22,%22text%22:%22MR%20%3Cwww.url.com%7Cname%3E%22%7D%7D%5D%7D
    Special characters are documented here: https://api.slack.com/reference/surfaces/formatting#escaping
    """
    text = re.sub(r"&(?!(amp|lt|gt);)", "&amp;", text)
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def format_project_name(event: Dict) -> str:
    project = event['project']
    project_name = project['path_with_namespace']
    project_url = project['web_url']
    return format_slack_link(project_url, project_name)


def format_author_name(event: Dict) -> str:
    author_name = event['user']['name']
    author_email = event['user']['email']
    slack_name = EMAIL_TO_SLACK_NAME.get(author_email)
    author_name = format_slack_text(author_name)
    if slack_name:
        slack_name = format_slack_text(slack_name)
        return f"<{slack_name}> ({author_name})"
    return author_name


def format_mr_title(mr: Dict) -> str:
    title = f"{mr['title']} (!{mr['iid']})"
    return f"MR {format_slack_link(mr['url'], title)}"
