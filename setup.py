from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='Gitlab Slack Notifier',
    version='1.0.0',
    url='https://github.com/heuritech/gitlab-slack-notifier',
    author='Heuritech Team',
    author_email='contact@heuritech.com',
    description=
    'Notify users on Slack when a change in GitLab concern them.',
    packages=["gitlabnotifier"],
    install_requires=required,
)
