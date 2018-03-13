import re

import attr
import click
import pybreaker
import requests

import crane
import crane.exc

from . import deployment, settings

session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=3)
session.mount('http://', _adapter)
session.mount('https://', _adapter)

time_breaker = pybreaker.CircuitBreaker(fail_max=20)


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

    @time_breaker
    def json(self):
        response = session.get(self.api_url, timeout=60)
        response.raise_for_status()
        return response.json()


@attr.s(frozen=True, slots=True)
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

    def service_from_name(self, name):
        response = session.get(
            '{url}/v1/projects/{env}/services'.format_map(settings),
            params={'name': name, 'stackId': self.id},
        )
        response.raise_for_status()
        service_info = response.json()['data'][0]
        return Service(service_info['id'], service_info['name'], self)


@attr.s(frozen=True, slots=True)
class Service(Entity):

    ID_PATTERN = re.compile('[0-9]s[0-9]+')
    stack = attr.ib(validator=attr.validators.instance_of(Stack))

    @property
    def web_url(self):
        return f'{self.stack.web_url}/services/{self.id}/containers'

    @property
    def api_url(self):
        return f'{settings["url"]}/v1/projects/{settings["env"]}/services/{self.id}'

    @property
    def launch_config(self):
        return self.json()['launchConfig']

    @property
    def sidekick_launch_configs(self):
        return {
            config['name']: config
            for config in self.json()['secondaryLaunchConfigs']
        }

    def start_upgrade(self):
        payload = {
            'inServiceStrategy': {
                'batchSize': settings['batch_size'],
                'intervalMillis': settings['batch_interval'] * 1000,
                'startFirst': settings['start_first'],
                'launchConfig': None,
                'secondaryLaunchConfigs': []
            }
        }

        if not settings['sidekick']:
            launch_config = payload['inServiceStrategy']['launchConfig'] = self.launch_config
        else:
            launch_config = self.sidekick_launch_configs[settings['sidekick']]
            payload['inServiceStrategy']['secondaryLaunchConfigs'].append(launch_config)

        launch_config['imageUuid'] = launch_config['imageUuid'].replace(deployment.old_version, deployment.new_version)

        click.echo(f'Upgrading {self.log_name}…')
        response = session.post(self.api_url, params={'action': 'upgrade'}, json=payload, timeout=60)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            try:
                response_payload = ex.response.json()
            except:
                response_payload = None

            if response_payload and response_payload.get('code') == 'ActionNotAvailable':
                message = (
                    f"Rancher won't let me upgrade {self.log_name} "
                    + click.style('(◕︿◕✿)', bold=True)
                    + f'\n\nPlease see if the service is upgradeable at {self.web_url}'
                )
            else:
                message = (
                    f"Upgrade failed, and I don't know why "
                    + click.style('(◍•﹏•)', bold=True)
                    + f'\n\nHere, maybe you will understand this:\n{ex.response.text}'
                )

            click.secho(message, err=True, fg='red')

            raise crane.exc.UpgradeFailed()

    def finish_upgrade(self):
        response = session.post(self.api_url, params={'action': 'finishupgrade'}, timeout=60, json={})
        response.raise_for_status()
        click.echo(f'Marked upgrade of {self.log_name} as finished in Rancher.')
