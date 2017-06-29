import re

from . import rancher, settings

ID_PATTERN = re.compile(r'^[0-9][a-z]{1,2}[0-9]+$')


def _get_stack_id(name):
    """Get the stack ID for the given stack name."""
    response = rancher.get(
        '{url}/v1/projects/{env}/environments'.format_map(settings),
        params={'name': name},
    )
    response.raise_for_status()

    return response.json()['data'][0]['id'].replace('1e', '1st')


def _get_service_id(name):
    """Get the service ID for the given service name."""
    response = rancher.get(
        '{url}/v1/projects/{env}/services'.format_map(settings),
        params={'name': name, 'stackId': settings['stack_id']},
    )
    response.raise_for_status()

    return response.json()['data'][0]['id']


def load_ids():
    """Set stack_id and service_id in the settings dict"""
    stack = settings['stack']
    settings['stack_id'] = stack if ID_PATTERN.match(stack) else _get_stack_id(stack)
    settings['service_ids'] = [
        service if ID_PATTERN.match(service) else _get_service_id(service)
        for service in settings['service']
    ]
