from collections import UserList
import json
from os import environ

import git
import requests

from .base import Base
from .. import deployment, settings

session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=3)
session.mount('http://', _adapter)
session.mount('https://', _adapter)


class AttachmentFields(UserList):
    """List subclass for working with Slack message attachment like dicts.

    So when you have fields like this::

        fields = [
            {'title': 'foo', 'value': 1, 'short': True},
            {'title': 'bar', 'value': 2, 'short': True},
        ]

    With this class you can::

        fields['foo'] = fields['bar'] * 10

    And the list will be edited to::

        fields = [
            {'title': 'foo', 'value': 20, 'short': True},
            {'title': 'bar', 'value': 2, 'short': True},
        ]
    """

    def __getitem__(self, item):
        for field in self.data:
            if field['title'] == item:
                return field['value']
        else:
            raise KeyError(f"'{item}' is not one of the fields")

    def __setitem__(self, item, value):
        for field in self.data:
            if field['title'] == item:
                field['value'] = value
                return
        else:
            self.data.append({'title': item, 'value': value, 'short': True})

    @classmethod
    def aslist(cls, obj):
        if isinstance(obj, cls):
            return obj.data
        raise TypeError()


class Hook(Base):

    def __init__(self):
        self.token = settings['slack_token']
        self.users_by_email = {
            user['profile'].get('email'): '@' + user['name']
            for user in session.get('https://slack.com/api/users.list', params={'token': self.token}).json()['members']
        }
        self.channels_by_name = {
            channel['name']: channel['id']
            for channel in session.get('https://slack.com/api/channels.list', params={'token': self.token}).json()['channels']
        }
        # The upcoming line is the most ridiculous, stupid, and effective hack I've ever written.
        # We create a link that has only a space as its link text, so it doesn't show up in Slack.
        # This allows us to store data in a fake URL, instead of needing a database or something.
        # Ridiculous.
        self.deployment_text = f'<{deployment.id}.com| >'
        self.channel_id = self.channels_by_name[settings['slack_channel']]

    @property
    def base_data(self):
        return {'token': self.token, 'channel': self.channel_id}

    def get_existing_message(self):
        response = session.get('https://slack.com/api/channels.history', params=self.base_data)
        messages = response.json()['messages']
        for message in messages:
            if message.get('text') == self.deployment_text:
                message['attachments'][0]['fields'] = AttachmentFields(message['attachments'][0]['fields'])
                return message

    def get_changelog(self):
        if deployment.is_redeploy:
            return 'Re-deploy without changes.'

        prefix = ''
        if deployment.is_rollback:
            prefix = ':warning: Rolling back the following changes:\n'

        return prefix + '\n'.join(
            (
                f'<{environ["CI_PROJECT_URL"]}/commit/{commit.hexsha}|{commit.summary}> '
                f'by {self.users_by_email.get(commit.author.email, commit.author.name)}'
            ) for commit in deployment.commits
        )

    def generate_new_message(self):
        fields = AttachmentFields()
        # setting empty fields to keep them in consistent order
        fields['Environment'] = ''
        fields['Branch'] = ''
        fields['Releaser'] = ''
        fields['Links'] = ' | '.join((
            f'<{environ["CI_REGISTRY_IMAGE"]}:{deployment.new_version}|Image>',
            f'<{deployment.stack.web_url}|Stack>',
        ))

        return {
            'link_names': True,
            'text': self.deployment_text,
            'attachments': [{
                'fallback': f'{environ["CI_PROJECT_PATH"]} release',
                'title': f'{environ["CI_PROJECT_PATH"]} release',
                'title_link': f'{environ["CI_PROJECT_URL"]}/builds/{environ["CI_JOB_ID"]}',
                'text': self.get_changelog(),
                'fields': fields,
            }],
        }

    def send_message(self, message):
        fields = message['attachments'][0]['fields']

        if ':no_entry_sign:' in fields['Environment']:
            message['attachments'][0]['color'] = 'danger'
        elif ':spinner:' in fields['Environment']:
            message['attachments'][0].pop('color', None)
        else:
            message['attachments'][0]['color'] = 'good'

        message['attachments'] = json.dumps(message['attachments'], default=AttachmentFields.aslist)
        if 'ts' in message:
            url = 'https://slack.com/api/chat.update'
            message['parse'] = True
        else:
            url = 'https://slack.com/api/chat.postMessage'
        session.post(url, data={**self.base_data, **message, 'link_names': '1'})

    def send_reply(self, message_id, text, in_channel=False):
        session.post(url, data={
            **self.base_data,
            'ts': message_id,
            'text': text,
            'reply_broadcast': 'true' if in_channel else 'false',
            'link_names': '1',
        })

    def set_status(self, message, status):
        fields = message['attachments'][0]['fields']
        env_lines = fields['Environment'].splitlines()
        for index, line in enumerate(env_lines):
            if line.startswith(self.env_text):
                env_lines[index] = self.env_text + ' ' + status
                break
        else:
            env_lines.append(self.env_text + ' ' + status)
        fields['Environment'] = '\n'.join(env_lines)

    def before_upgrade(self):
        message = self.get_existing_message() or self.generate_new_message()

        if message['ts']:
            self.send_reply(message['ts'], f'Releasing also on {self.env_text}.')

        self.set_status(message, ':spinner:')
        message['attachments'][0]['fields']['Releaser'] = self.users_by_email.get(
            environ["GITLAB_USER_EMAIL"], environ["GITLAB_USER_EMAIL"]
        )
        message['attachments'][0]['fields']['Branch'] = (
            (':warning: ' if environ['CI_COMMIT_REF_NAME'] != 'master' else '')
            + f'<{environ["CI_PROJECT_URL"]}/tree/{environ["CI_COMMIT_REF_NAME"]}|{environ["CI_COMMIT_REF_NAME"]}>'
        )
        self.send_message(message)

    def after_upgrade_success(self):
        message = self.get_existing_message()
        self.set_status(message, ':white_check_mark:')
        self.send_message(message)
        self.send_reply(message['ts'], f'Released on {self.env_text}.')

    def after_upgrade_failure(self):
        message = self.get_existing_message()
        self.set_status(message, ':x:')
        self.send_message(message)
        self.send_reply(message['ts'], f'Release failed on {self.env_text}.', in_channel=True)

    @property
    def is_active(self):
        return 'slack_token' in settings and 'slack_channel' in settings

    @property
    def env_text(self):
        if 'CI_ENVIRONMENT_URL' in environ:
            return f'<{environ["CI_ENVIRONMENT_URL"]}|{environ["CI_ENVIRONMENT_NAME"]}>'
        else:
            return environ['CI_ENVIRONMENT_NAME']
