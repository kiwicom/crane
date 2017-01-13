import requests
import json
from structlog import get_logger
import click
import time

glog = get_logger()
glog.bind(time=time.time())

@click.command()
@click.option('--rancher-url', envvar='RANCHER_URL', required=True)
@click.option('--access', envvar='RANCHER_ACCESS_KEY', required=True)
@click.option('--secret', envvar='RANCHER_SECRET_KEY', required=True)
@click.option('--project', envvar='RANCHER_PROJECT_ID', required=True)
@click.option('--service', envvar='RANCHER_SERVICE_ID', required=True)
@click.option('--new-image', envvar='RANCHER_SERVICE_IMAGE', default=None)
@click.option('--batch-size', envvar='RANCHER_BATCH_SIZE', default=1)
@click.option('--batch-interval', envvar='RANCHER_BATCH_INTERVAL', default=2)
@click.option('--start-first', envvar='RANCHER_START_FIRST', default=False, is_flag=True)
@click.option('--sidekick', envvar='RANCHER_SIDEKICK_NAME', default=None)
def main(rancher_url, access, secret, project, service, new_image, batch_size, batch_interval, start_first, sidekick):

    log = glog.bind(project=project, service=service, new_image=new_image, sidekick=sidekick)

    if sidekick:
        launch_config = None
        secondary_launch_config = get_launch_config(rancher_url, access, secret, project, service, sidekick)
        if new_image:
            secondary_launch_config[0]['imageUuid'] = 'docker:{0}'.format(new_image)
    else:
        launch_config = get_launch_config(rancher_url, access, secret, project, service, sidekick)
        secondary_launch_config = []
        if new_image:
            launch_config['imageUuid'] = 'docker:{0}'.format(new_image)

    request_body = {
        'inServiceStrategy': {
            'batchSize': batch_size,
            'intervalMillis': batch_interval * 1000,
            'startFirst': start_first,
            'launchConfig': launch_config,
            'secondaryLaunchConfigs': secondary_launch_config
        }
    }
    log.info(event='upgrading')
    api_url = '{0}/v1/projects/{1}/services/{2}/?action=upgrade'.format(rancher_url, project, service)
    r = requests.post(api_url, auth=(access, secret), timeout=60, json=request_body)
    r.raise_for_status()
    response = json.loads(r.text)

    service_url = response['links']['self']
    service_upgraded = False

    while service_upgraded is False:
        r = requests.get(service_url, auth=(access, secret), timeout=60)
        r.raise_for_status()
        response = json.loads(r.text)
        if response['state'] == 'upgrading':
            log.info(event='wait_for_upgrade', state=response['state'])
            time.sleep(3)
            continue
        service_upgraded = True

    if response['state'] == 'upgraded':
        r = requests.post(response['actions']['finishupgrade'], auth=(access, secret), timeout=60, json={})
        r.raise_for_status()
        log.info(event='upgraded')


def get_launch_config(url, access, secret, project, service, sidekick=None):
    api_url = '{0}/v1/projects/{1}/services/{2}'.format(url, project, service)

    r = requests.get(api_url, auth=(access, secret), timeout=60)
    r.raise_for_status()

    response = json.loads(r.text)
    if sidekick:
        return [d for d in response['secondaryLaunchConfigs'] if d['name'] == sidekick]
    else:
        return response['launchConfig']


if __name__ == '__main__':
    main()