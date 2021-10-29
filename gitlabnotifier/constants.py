import os

X_GITLAB_TOKEN = os.environ.get('X_GITLAB_TOKEN')
GITLAB_BASE_URL = os.environ.get('GITLAB_BASE_URL')
GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN')
GITLAB_HEADERS = {'Private-Token': GITLAB_TOKEN}

SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')

GLOBAL_CHANEL = '#_gitlab'
DEV_CHANEL = '#_gitlab_debug'
FLASK_ENV = os.environ.get('FLASK_ENV')
