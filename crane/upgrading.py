import time

import click

from . import rancher, settings


def get_launch_config(service_id):
    response = rancher.get(f'{settings["url"]}/v1/projects/{settings["env"]}/services/{service_id}', timeout=60)
    response.raise_for_status()
    return response.json()['launchConfig']


def get_sidekick_launch_config(service_id, sidekick):
    response = rancher.get(f'{settings["url"]}/v1/projects/{settings["env"]}/services/{service_id}', timeout=60)
    response.raise_for_status()
    return next(config for config in response.json()['secondaryLaunchConfigs'] if config['name'] == sidekick)


def request_upgrade(service_id, upgrade_request):
    click.echo(f'Upgrading {service_id}…')
    response = rancher.post(
        f'{settings["url"]}/v1/projects/{settings["env"]}/services/{service_id}',
        params={'action': 'upgrade'},
        json=upgrade_request,
        timeout=60,
    )
    response.raise_for_status()
    service_url = response.json()['links']['self']

    while True:
        response = rancher.get(service_url, timeout=60)
        response.raise_for_status()
        if response.json()['state'] != 'upgrading':
            click.echo(f"Rancher says {service_id} is now '{response.json()['state']}'.")
            return response.json()

        time.sleep(3)


def upgrade(service_id):
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
        launch_config = request['inServiceStrategy']['launchConfig'] = get_launch_config(service_id)
    else:
        launch_config = get_sidekick_launch_config(service_id, settings['sidekick'])
        request['inServiceStrategy']['secondaryLaunchConfigs'].append(launch_config)

    if settings['new_image']:
        launch_config['imageUuid'] = 'docker:{new_image}'.format_map(settings)

    response = request_upgrade(service_id, request)

    if settings['sleep_after_upgrade']:
        click.echo(f'Upgrade of {service_id} done, waiting {settings["sleep_after_upgrade"]}s as requested ' + click.style('(ʃƪ˘･ᴗ･˘)', bold=True))
        time.sleep(settings.sleep_after_upgrade)

    if not settings['manual_finish'] and response['state'] == 'upgraded':
        response = rancher.post(response['actions']['finishupgrade'], timeout=60, json={})
        response.raise_for_status()
        click.echo(f'Marked upgrade of {service_id} as finished.')
