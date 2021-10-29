from contextlib import ExitStack
from unittest import mock

import pytest

from gitlabnotifier.process_gitlab_notif import \
    get_messages_and_emails_from_event


def mock_get_mr_discussion(project_id, mr_id, discussion_id, **kwargs):
    if discussion_id == "good":
        return {
            "notes":
                [
                    {"author": {"id": "test1"}},
                    {"author": {"id": "test2"}},
                    {"author": {"id": "test1"}},
                    {"author": {"id": "test3"}}
                ]
        }  # yapf: disable
    if discussion_id == "none":
        return {"notes": [{"author": {"id": "test3"}}]}
    raise NotImplementedError(discussion_id)


def mock_get_user(user_id, **kwargs):
    if user_id == "test1":
        return {"email": "test1@gmail.com"}
    if user_id == "test2":
        return {"email": "foobar2@heuri.fr"}
    if user_id == "test3":
        return {"email": "hello_there@mycompany.com"}
    if user_id == "test4":
        return {"email": "test4@gmail.com"}
    raise NotImplementedError(user_id)


def mock_get_user_by_username(username, **kwargs):
    if username == "Michael Scott":
        return [{"email": "test1@gmail.com"}]
    if username == "test2":
        return [{"email": "foobar2@heuri.fr"}]
    if username == "Test3":
        return [{"email": "hello_there@mycompany.com"}]
    if username == "Test4":
        return [{"email": "test4@gmail.com"}]
    return []


def mock_get_mr(project_id, mr_id, **kwargs):
    if mr_id == 2:
        return {"author": {"id": "test1"}}
    raise NotImplementedError(project_id, mr_id)


def mock_get_mr_participants(project_id, mr_id, **kwargs):
    if mr_id == 5:
        return [{"id": "test1"}, {"id": "test2"}, {"id": "test3"}]
    raise NotImplementedError(project_id, mr_id)

@pytest.mark.parametrize(
    "event,expected_message,expected_user_emails", [
        pytest.param({
                'object_kind': 'note',
                'project_id': 119,
                'project': {
                    'path_with_namespace': 'mycompany/myproject',
                    'web_url': 'https://project',
                },
                # the author of the comment that triggered the event
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                'object_attributes': {'discussion_id': 'none', 'url': 'http://myurl', 'description': 'tata'},
                'merge_request': {'iid': 2, 'assignee_ids': [], 'title': 'THE MR', 'url': 'http://mr'},
            },
            {
                'attachments': [{'text': 'tata'}],
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!2)> '
                        '> :writing_hand: <http://myurl|Commented> by test3:',
            },
            {"test1@gmail.com"},  # the author of the MR
            id="single user in discussion -> notify MR's author"
        ),
        pytest.param({
                'object_kind': 'note',
                'project_id': 119,
                'project': {
                    'path_with_namespace': 'mycompany/myproject',
                    'web_url': 'https://project',
                },
                # the author of the comment that triggered the event
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                'object_attributes': {'discussion_id': 'none', 'url': 'http://myurl', 'description': '@test2 tata'},
                'merge_request': {'iid': 2, 'assignee_ids': [], 'title': 'THE MR', 'url': 'http://mr'},
            },
            {
                'attachments': [{'text': '@test2 tata'}],
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!2)> '
                        '> :writing_hand: <http://myurl|Commented> by test3:',
            },
            {"test1@gmail.com", "foobar2@heuri.fr"},
            id="single user in discussion with mention -> notify MR's author and mentionned"
        ),
        pytest.param(
            {
                'object_kind': 'note',
                'project_id': 119,
                'project': {
                    'path_with_namespace': 'mycompany/myproject',
                    'web_url': 'https://project',
                },
                # the author of the comment that triggered the event
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                'object_attributes': {'discussion_id': 'good', 'url': 'http://myurl', 'description': 'check this'},
                'merge_request': {'iid': 2, 'assignee_ids': [], 'title': 'THE MR', 'url': 'http://mr'},
            },
            {
                'attachments': [{'text': 'check this'}],
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!2)> '
                        '> :writing_hand: <http://myurl|Commented> by test3:',
            },
            {"foobar2@heuri.fr", "test1@gmail.com"},
            id="multiple users in discussion, and excluding the one who put the last comment"
        ),
        pytest.param(
            {
                'object_kind': 'note',
                'project_id': 119,
                'project': {
                    'path_with_namespace': 'mycompany/myproject',
                    'web_url': 'https://project',
                },
                # the author of the comment that triggered the event
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                'object_attributes': {'discussion_id': 'good', 'url': 'http://myurl', 'description': '@Test4 check this'},
                'merge_request': {'iid': 2, 'assignee_ids': [], 'title': 'THE MR', 'url': 'http://mr'},
            },
            {
                'attachments': [{'text': '@Test4 check this'}],
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!2)> '
                        '> :writing_hand: <http://myurl|Commented> by test3:',
            },
            {"foobar2@heuri.fr", "test1@gmail.com", "test4@gmail.com"},
            id="multiple users in discussion with mention, and excluding the one who put the last comment"
        ),
        pytest.param({
                'object_kind': 'merge_request',
                'project': {
                    'id': 119,
                    'path_with_namespace': 'mycompany/myproject',
                    'web_url': 'https://project',
                },
                # the author of the comment that triggered the event
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                'object_attributes': {'iid': 2, 'action': 'approved', 'title': 'THE MR', 'url': 'http://mr'},
            },
            {
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!2)> '
                        '> :+1: Approved by test3',
                },
            {"test1@gmail.com"},
            id="MR opened by test1, approved by test3"
        ),
        pytest.param({
                'object_kind': 'merge_request',
                'project': {
                    'id': 119,
                    'path_with_namespace': 'mycompany/myproject',
                    'web_url': 'https://project',
                },
                # the author of the comment that triggered the event
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                'object_attributes': {'iid': 5, 'action': 'merge', 'title': 'THE MR', 'url': 'http://mr'},
            },
            {
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!5)> '
                        '> :tada: Merged by test3'
            },
            {"test1@gmail.com", "foobar2@heuri.fr", "hello_there@mycompany.com"},
            id="MR merged by test3. test1, test3 and test2 participated"
        ),
        pytest.param({
                "object_kind": "merge_request",
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                "project": {"id": 73, 'path_with_namespace': 'mycompany/myproject', 'web_url': 'https://project'},
                "object_attributes": {"assignee_id": "test2", "iid": 5, 'url': 'http://mr', 'title': 'THE MR'},
                "changes": {
                    "assignees": {
                        "previous": [],
                        "current": [{"username": "toto"}]
                    }
                },
            },
            {
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!5)> '
                        '> :point_down: This MR was assigned to you'
            },
            {"foobar2@heuri.fr"},
            id="test2 was assigned an MR by Obi Wan"
        ),
        pytest.param({
                "object_kind": "merge_request",
                'user': {'name': 'test3', 'email': 'hello_there@mycompany.com'},
                "project": {"id": 73, 'path_with_namespace': 'mycompany/myproject', 'web_url': 'https://project'},
                "object_attributes": {"assignee_id": "test2", "iid": 5, 'url': 'http://mr', 'title': 'THE MR'},
                "changes": {},
            },
            {},
            set(),
            id="There is an update of the MR that is not an assignment to the MR assigned to test2"
        ),
        pytest.param({
                "object_kind": "merge_request",
                'user': {'name': 'test2', 'email': "foobar2@heuri.fr"},
                "project": {"id": 73, 'path_with_namespace': 'mycompany/myproject', 'web_url': 'https://project'},
                "object_attributes": {"assignee_id": "test2", "iid": 5, 'url': 'http://mr', 'title': 'THE MR'},
                "changes": {
                    "assignees": {
                        "previous": [],
                        "current": [{"username": "toto"}]
                    }
                },
            },
            {
                'text': '<https://project|mycompany/myproject> '
                        '> MR <http://mr|THE MR (!5)> '
                        '> :point_down: This MR was assigned to you'
            },
            set(),
            id="test2 self assigned the MR"
        ),
        pytest.param({
                "object_kind": "merge_request",
                "project": {"id": 73},
                "object_attributes": {"assignee_id": None, "iid": 486}
            },
            {},
            set(),
            id="A user was unassigned MR 486"
        )
    ]
) # yapf: disable
@mock.patch(
    "gitlabnotifier.process_gitlab_notif.get_mr_discussion", side_effect=mock_get_mr_discussion
)
@mock.patch("gitlabnotifier.process_gitlab_notif.get_user", side_effect=mock_get_user)
@mock.patch(
    "gitlabnotifier.process_gitlab_notif.get_user_by_username",
    side_effect=mock_get_user_by_username
)
@mock.patch("gitlabnotifier.process_gitlab_notif.get_mr", side_effect=mock_get_mr)
@mock.patch(
    "gitlabnotifier.process_gitlab_notif.get_mr_participants", side_effect=mock_get_mr_participants
)
def test_get_user_emails_from_event(
    _mock1, _mock2, _mock3, _mock4, _mock5, event, expected_message, expected_user_emails
):
    with ExitStack() as context:
        if expected_message is None:
            context.enter_context(pytest.raises(ValueError))
        message, user_emails = get_messages_and_emails_from_event(event)
        assert message == expected_message
        assert user_emails == expected_user_emails
