import os
from unittest import mock

import api
import requests

ENVS = {'X_GITLAB_TOKEN': 'secret'}


def test_x_gitlab_no_token():
    with api.run():
        res = requests.get('http://localhost:5000/')
        res.raise_for_status()


@mock.patch.dict(os.environ, ENVS)
def test_x_gitlab_no_valid_token():
    with api.run():
        res = requests.get('http://localhost:5000/')
        assert res.status_code == 403


@mock.patch.dict(os.environ, ENVS)
def test_x_gitlab_valid_token():
    headers = {"x-gitlab-token": ENVS['X_GITLAB_TOKEN']}
    with api.run():
        res = requests.get('http://localhost:5000/', headers=headers)
        res.raise_for_status()
