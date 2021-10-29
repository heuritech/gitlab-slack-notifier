"""Wrapper for the GitLab API. Official documentation can be found here: https://docs.gitlab.com/ee/api/README.html"""

import os
from typing import Dict

import requests

from gitlabnotifier.constants import GITLAB_BASE_URL, GITLAB_HEADERS


def _call_api(suffix: str):
    url = os.path.join(GITLAB_BASE_URL, "api/v4", suffix)
    response = requests.get(url, headers=GITLAB_HEADERS)
    response.raise_for_status()
    return response


def get_user(user_id: str):
    """https://docs.gitlab.com/ee/api/users.html#for-user"""
    return _call_api(f"users/{user_id}").json()


def get_user_by_username(username: str):
    """https://docs.gitlab.com/ee/api/users.html#for-user"""
    return _call_api(f"users?username={username}").json()


def _call_project_api(project_id: str, suffix: str):
    return _call_api(os.path.join("projects", str(project_id), suffix))


def get_job_trace(project_id: str, job_id: str):
    return _call_project_api(project_id, f"jobs/{job_id}/trace").text


## MR API


def _call_mr_api(project_id: str, mr_id: str, suffix: str):
    return _call_project_api(project_id, os.path.join(f"merge_requests/{mr_id}", suffix))


def get_mr(project_id: str, mr_id: str):
    """https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr"""
    response = _call_mr_api(project_id, mr_id, "")
    return response.json()


def get_mr_participants(project_id: str, mr_id: str):
    """https://docs.gitlab.com/ee/api/merge_requests.html#get-single-mr-participants"""
    response = _call_mr_api(project_id, mr_id, "participants")
    return response.json()


def get_mr_discussion(project_id: str, mr_id: str, discussion_id: str) -> Dict:
    """https://docs.gitlab.com/ee/api/discussions.html#get-single-merge-request-discussion-item"""
    response = _call_mr_api(project_id, mr_id, f"discussions/{discussion_id}")
    return response.json()
