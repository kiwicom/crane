import requests
import json
import time


def rancher_api_get(url, access, secret):
    r = requests.get(url, auth=(access, secret), timeout=60)
    r.raise_for_status()
    return json.loads(r.text)


def _get_launch_config(url, access, secret, project, service, sidekick=None):
    api_url = f'{url}/v1/projects/{project}/services/{service}'

    response = rancher_api_get(api_url, access, secret)
    if sidekick:
        return [d for d in response['secondaryLaunchConfigs'] if d['name'] == sidekick]
    else:
        return response['launchConfig']


def get_launch_configs(rancher_url, env, service, sidekick, new_image, access, secret):
    if sidekick:
        launch_config = None
        secondary_launch_config = _get_launch_config(rancher_url, access, secret, env, service, sidekick)
        if new_image:
            secondary_launch_config[0]['imageUuid'] = f'docker:{new_image}'
    else:
        launch_config = _get_launch_config(rancher_url, access, secret, env, service, sidekick)
        secondary_launch_config = []
        if new_image:
            launch_config['imageUuid'] = f'docker:{new_image}'

    return launch_config, secondary_launch_config


def upgrade(rancher_url, env, service, upgrade_request, sleep_after_upgrade, no_finish_upgrade, log, access, secret):
    log.info(event='upgrading')
    api_url = f'{rancher_url}/v1/projects/{env}/services/{service}/?action=upgrade'
    r = requests.post(api_url, auth=(access, secret), timeout=60, json=upgrade_request)
    r.raise_for_status()
    response = json.loads(r.text)

    service_url = response['links']['self']
    service_upgraded = False

    while not service_upgraded:
        response = rancher_api_get(service_url, access, secret)

        if response['state'] == 'upgrading':
            log.info(event='wait_for_upgrade', state=response['state'])
            time.sleep(3)
            continue
        service_upgraded = True

    if sleep_after_upgrade:
        log.info(event='sleep_after_upgrade', length=sleep_after_upgrade)
        time.sleep(sleep_after_upgrade)

    if no_finish_upgrade is False and response['state'] == 'upgraded':
        r = requests.post(response['actions']['finishupgrade'], auth=(access, secret), timeout=60, json={})
        r.raise_for_status()
        log.info(event='upgraded')


def get_upgrade_request(batch_size, batch_interval, start_first, launch_config, secondary_launch_config):
    upgrade_request = {
        'inServiceStrategy': {
            'batchSize': batch_size,
            'intervalMillis': batch_interval * 1000,
            'startFirst': start_first,
            'launchConfig': launch_config,
            'secondaryLaunchConfigs': secondary_launch_config
        }
    }

    return upgrade_request
