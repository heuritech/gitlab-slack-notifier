Gitlab Slack Notifier
======================

Webservice that notifies users on Slack when a change in GitLab concern them.

Setup
======

## Slack

Create a Slack app, go to "OAuth & Permissions" page,
add the following permissions to "Bot Token Scopes":
- `users:read`
- `users.profile:read`
- `chat:write`
- `chat:write.public`

Then click "Install to Workspace" and confirm.
Copy the "Bot User OAuth Token", will be put into `SLACK_API_TOKEN`

## Gitlab

You'll require a `GITLAB_TOKEN` with admin rights on Gitlab (read only is sufficient).
Ask it to one of the maintainers of your Gitlab instance.

To enable this notifier on one of your projects, go to: `(Your repo) > Settings > Webhooks`

You have to set:
  - URL: the Gitlab URL you'll listen to (e.g., `http://gitlab.mycompany.com`)
  - Secret Token: Gitlab secret token, which you will give to the webservice for authenticating
  - Tick the following events:
    - Comments
    - Issues
    - Merge request
    - Job
    - Pipeline
  - Click on `Add webhook`


Launch
======

## Webservice

To build the Docker and launch the webservice:
```bash
export GITLAB_TOKEN="your-gitlab-token"
export SLACK_API_TOKEN="your-slack-api-token"
HOST=127.0.0.1 PORT=5000 make build-docker run-docker
```

Contributors
============

At first, this project has been implemented within [Heuritech](https://www.heuritech.com/) for an internal usage 
and then open sourced to GitHub.
The original git history hasn't been copied during this migration.
Thus, the [initial commit](https://github.com/heuritech/gitlab-slack-notifier/commit/64d14d1f68102f05bfd1879b328be003b341451c)
is a copy of Heuritech's internal version, without the code specific to our company.

Contributors of the original repository are:
- [Didier Marin](https://github.com/didmar)
- [Henri Hannetel](https://github.com/HenriTEL)
- [Antoine Hoorelbeke](https://github.com/anth2o)
