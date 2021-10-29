from typing import Dict, Set, Tuple

from werkzeug.exceptions import HTTPException

from gitlabnotifier.constants import GITLAB_BASE_URL
from gitlabnotifier.format import (format_author_name, format_mr_title,
                                   format_project_name, format_slack_link,
                                   format_slack_text)
from gitlabnotifier.gitlab_api import (get_job_trace, get_mr,
                                       get_mr_discussion, get_mr_participants,
                                       get_user, get_user_by_username)


def status_requires_notification(event):
    attributes = event['object_attributes']
    status = attributes['status']
    return status not in ['success', 'running', 'pending', 'canceled']


def event_is_assignement(event: Dict):
    if event["object_attributes"].get("assignee_id") is None:
        return False
    assignees_change = event.get("changes", {}).get("assignees", {})
    # NOTE: we don't have to inspect what really is assignees_change, because we already know with
    # `event["object_attributes"].get("assignee_id")` who the assignee is
    # we just have to check that there is a change in the assignees, so that we are sure that this
    # event corresponds to an assignment, and not to an other update of the MR
    return {user["username"] for user in assignees_change.get("current", [])
           } != {user["username"] for user in assignees_change.get("previous", [])}


def get_messages_and_emails_from_event(event: Dict) -> Tuple[Dict, Set[str]]:
    if event['object_kind'] == 'pipeline' and status_requires_notification(event):
        return generate_pipeline_message(event), {event['user']['email']}
    if event['object_kind'] == 'note':
        return generate_note_message(event), get_users_emails_from_event_note(event)
    if event['object_kind'] == 'merge_request':
        if event["object_attributes"].get("action") == "approved":
            return generate_approval_message(event), get_users_emails_from_event_approval(event)
        if event["object_attributes"].get("action") == "merge":
            return generate_merge_message(event), get_users_emails_from_event_merge(event)
        if event_is_assignement(event):
            return generate_assignee_message(event), get_users_emails_from_event_assignee(event)
    return {}, set()


# PIPELINE


def extract_lint_errors(trace):
    for line in trace.split('\n'):
        if "[E" in line:
            yield line.rstrip()


def extract_pytest_fails(trace):
    failures_block = False
    for line in trace.split('\n'):
        if line.startswith('=================================== FAILURES'):
            failures_block = True
            continue
        elif failures_block and line.startswith('======================'):
            failures_block = False
        if failures_block:
            yield line


def generate_pipeline_message(j):
    attributes = j['object_attributes']
    status = attributes['status']
    pipeline_id = attributes['id']
    project_id = j['project']['id']
    project_url = j['project']['web_url']
    project_name = j['project']['path_with_namespace']
    commit_id = j['commit']['id']
    commit_url = j['commit']['url']
    pipeline_url = f"{project_url}/pipelines/{pipeline_id}"

    failures = []
    for build in j['builds']:
        if build['status'] == "failed":
            job_id = build['id']
            if build['stage'] in ['lint', 'test']:
                trace = get_job_trace(project_id, job_id)
                if build['stage'] == 'lint':
                    errors = list(extract_lint_errors(trace))
                    error_details = "\n".join(errors)
                else:
                    errors = list(extract_pytest_fails(trace))
                    error_details = "\n".join(errors)
            else:
                error_details = "(no details)"
            pretext = "Job %s failed" % build['name']
            failure = {
                "pretext": pretext,
                "text": format_slack_text(error_details),
                "link": "%s/%s/-/jobs/%d" % (GITLAB_BASE_URL, project_name, job_id)
            }
            failures.append(failure)

    main_message = f"{format_project_name(j)} > {format_slack_link(commit_url, commit_id[:6])} > " \
                   f"Pipeline {format_slack_link(pipeline_url, f'#{pipeline_id}')} ran with status {status}"

    return {
        "text":
            main_message,
        "attachments":
            [
                {
                    "fallback": failure['pretext'],
                    "color": "#ff0000",
                    "title": failure['pretext'],
                    "title_link": failure['link'],
                    "text": failure['text']
                } for failure in failures
            ]
    }


# MERGE REQUEST COMMENT


def generate_note_message(j):
    attributes = j['object_attributes']
    comment = attributes['description']
    link = attributes['url']
    return {
        "text":
            f"{format_project_name(j)} > "
            f"{format_mr_title(j['merge_request'])} > "
            f":writing_hand: {format_slack_link(link, 'Commented')} by {format_author_name(j)}:",
        "attachments": [{
            "text": format_slack_text(comment)
        }]
    }


def get_users_emails_from_event_note(event: Dict) -> Set[str]:
    mr = get_mr(event["project_id"], event["merge_request"]["iid"])
    user_id = mr["author"]["id"]
    discussion = get_mr_discussion(
        event["project_id"], event["merge_request"]["iid"],
        event["object_attributes"]["discussion_id"]
    )
    in_discussion_user_ids = {note["author"]["id"] for note in discussion["notes"]}
    in_discussion_user_ids.add(user_id)  # we add the author of the MR if he isn't in the discussion
    user_emails = {get_user(user_id)["email"] for user_id in in_discussion_user_ids}
    # we don't want to notify the person who triggered the comment even if he's in the discussion
    # we have to remove it by email and not by ID,
    # because the ID isn't available in event["user"]["email"]
    user_emails.remove(event["user"]["email"])
    user_emails.update(get_mentionned_user_emails(event))
    return user_emails


def get_mentionned_user_emails(event: Dict) -> Set[str]:
    user_emails = set()
    comment = event['object_attributes']['description']
    if "@" in comment:
        mentionned_user_names = [x.split(" ")[0] for x in comment.split("@")[1:]]
        mentionned_user_names = [user_name for user_name in mentionned_user_names if user_name]
        for user_name in mentionned_user_names:
            users = get_user_by_username(user_name)
            if len(users) == 0:
                print(f"No user found with user name {user_name}")
                continue
            if len(users) > 1:
                raise ValueError(
                    f"Multiple users found with user name {user_name}. How is this possible ?"
                )
            user_emails.add(users[0]["email"])
    return user_emails


# MERGE REQUEST APPROVAL


def generate_approval_message(event: Dict) -> Dict[str, str]:
    assert event["object_attributes"]["action"] == "approved"
    return {
        "text":
            f"{format_project_name(event)} > "
            f"{format_mr_title(event['object_attributes'])} > "
            f":+1: Approved by {format_author_name(event)}"
    }


def get_users_emails_from_event_approval(event: Dict) -> Set[str]:
    mr = get_mr(event["project"]["id"], event["object_attributes"]["iid"])
    user_id = mr["author"]["id"]
    return {get_user(user_id)["email"]}


# MERGE REQUEST MERGED


def generate_merge_message(event: Dict) -> Dict[str, str]:
    assert event["object_attributes"]["action"] == "merge"
    return {
        "text":
            f"{format_project_name(event)} > "
            f"{format_mr_title(event['object_attributes'])} > "
            f":tada: Merged by {format_author_name(event)}"
    }


def get_users_emails_from_event_merge(event: Dict) -> Set[str]:
    mr_participant_ids = [
        user["id"]
        for user in get_mr_participants(event["project"]["id"], event["object_attributes"]["iid"])
    ]
    mr_participant_emails = {get_user(user_id)["email"] for user_id in mr_participant_ids}
    # we used to remove the email of the person who merged the MR because it seemed useless to notify him
    # nonetheless, it is useful since we often use the feature "Merge when pipeline succeeds"
    return mr_participant_emails


# ASSIGNEE TO MR


def generate_assignee_message(event: Dict) -> Dict[str, str]:
    return {
        "text":
            f"{format_project_name(event)} > "
            f"{format_mr_title(event['object_attributes'])} > "
            f":point_down: This MR was assigned to you"
    }


def get_users_emails_from_event_assignee(event: Dict) -> Set[str]:
    return {get_user(event['object_attributes']["assignee_id"])["email"]} - {event["user"]["email"]}
