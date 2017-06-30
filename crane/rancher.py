import re
import sys
import time

import attr
import click
import requests

from . import settings


session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=3)
session.mount('http://', _adapter)
session.mount('https://', _adapter)


class UpgradeFailed(Exception):
    pass


@attr.s(frozen=True, slots=True)
class Entity:

    id = attr.ib()
    name = attr.ib(validator=attr.validators.instance_of(str))

    @id.validator
    def validate_rancher_id(self, attribute, value):
        if not self.ID_PATTERN.match(value):
            raise ValueError('the Rancher ID seems incorrectly formatted')

    @property
    def log_name(self):
        return click.style(self.name, bold=True)

    @property
    def json(self):
        response = session.get(self.api_url, timeout=60)
        response.raise_for_status()
        return response.json()

class Stack(Entity):

    ID_PATTERN = re.compile('[0-9]st[0-9]+')

    @property
    def web_url(self):
        return f'{settings["url"]}/env/{settings["env"]}/apps/stacks/{self.id}'

    @property
    def api_url(self):
        return f'{settings["url"]}/v1/projects/{settings["env"]}/environments/{self.id}'

    @classmethod
    def from_name(cls, name):
        response = session.get(
            '{url}/v1/projects/{env}/environments'.format_map(settings),
            params={'name': name},
        )
        response.raise_for_status()
        stack_info = response.json()['data'][0]

        return cls(stack_info['id'].replace('1e', '1st'), stack_info['name'])


class Service(Entity):

    ID_PATTERN = re.compile('[0-9]s[0-9]+')

    @classmethod
    def from_name(cls, name):
        response = session.get(
            '{url}/v1/projects/{env}/services'.format_map(settings),
            params={'name': name, 'stackId': settings['stack'].id},
        )
        response.raise_for_status()
        service_info = response.json()['data'][0]

        return cls(service_info['id'], service_info['name'])

    @property
    def web_url(self):
        return f'{settings["stack"].web_url}/services/{self.id}/containers'

    @property
    def api_url(self):
        return f'{settings["url"]}/v1/projects/{settings["env"]}/services/{self.id}'

    @property
    def launch_config(self):
        return self.json['launchConfig']

    @property
    def sidekick_launch_configs(self):
        return {
            config['name']: config
            for config in self.json['secondaryLaunchConfigs']
        }

    def request_upgrade(self, body):
        click.echo(f'Upgrading {self.log_name}…')
        response = session.post(self.api_url, params={'action': 'upgrade'}, json=body, timeout=60)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            if ex.response.json()['code'] == 'ActionNotAvailable':
                click.secho(f"Rancher won't let me upgrade {self.log_name} " + click.style('(◕︿◕✿)', bold=True), err=True, fg='red')
                click.secho(f'Please see if the service is upgradeable at {self.web_url}', err=True, fg='red')
            else:
                click.secho(f"Upgrade failed, and I don't know why " + click.style('(◍•﹏•)', bold=True), err=True, fg='red')
                click.secho(f"Here, maybe you will understand this:\n{json.dumps(ex.response.json(), indent=2)}" , err=True, fg='red')

            raise UpgradeFailed()

        service_url = response.json()['links']['self']

        while True:
            response = session.get(service_url, timeout=60)
            response.raise_for_status()
            if response.json()['state'] != 'upgrading':
                click.echo(f"Rancher says {self.log_name} is now '{response.json()['state']}'.")
                return response.json()

            time.sleep(3)

    def upgrade(self):
        request = {
            'inServiceStrategy': {
                'batchSize': settings['batch_size'],
                'intervalMillis': settings['batch_interval'] * 1000,
                'startFirst': settings['start_first'],
                'launchConfig': None,
                'secondaryLaunchConfigs': []
            }
        }

        if not settings['sidekick']:
            launch_config = request['inServiceStrategy']['launchConfig'] = self.launch_config
        else:
            launch_config = self.sidekick_launch_configs[settings['sidekick']]
            request['inServiceStrategy']['secondaryLaunchConfigs'].append(launch_config)

        if settings['new_image']:
            launch_config['imageUuid'] = 'docker:{new_image}'.format_map(settings)

        response = self.request_upgrade(request)

        if settings['sleep_after_upgrade']:
            click.echo(f'Upgrade of {self.log_name} done, waiting {settings["sleep_after_upgrade"]}s as requested ' + click.style('(ʃƪ˘･ᴗ･˘)', bold=True))
            time.sleep(settings['sleep_after_upgrade'])

        if not settings['manual_finish'] and response['state'] == 'upgraded':
            response = session.post(response['actions']['finishupgrade'], timeout=60, json={})
            response.raise_for_status()
            click.echo(f'Marked upgrade of {self.log_name} as finished in Rancher.')
