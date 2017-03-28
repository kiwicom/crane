from structlog import get_logger
import click
import time
from . import utils, ids

glog = get_logger()
glog.bind(time=time.time())


@click.command()
@click.option('--rancher-url', envvar='RANCHER_URL', required=True)
@click.option('--access', envvar='RANCHER_ACCESS_KEY', required=True)
@click.option('--secret', envvar='RANCHER_SECRET_KEY', required=True)
@click.option('--project', envvar='RANCHER_PROJECT_ID', required=True)
@click.option('--stack', envvar='RANCHER_STACK_NAME', required=False)
@click.option('--service', envvar='RANCHER_SERVICE_ID', required=True)
@click.option('--new-image', envvar='RANCHER_SERVICE_IMAGE', default=None)
@click.option('--batch-size', envvar='RANCHER_BATCH_SIZE', default=1)
@click.option('--batch-interval', envvar='RANCHER_BATCH_INTERVAL', default=2)
@click.option('--start-first', envvar='RANCHER_START_FIRST', default=False, is_flag=True)
@click.option('--sidekick', envvar='RANCHER_SIDEKICK_NAME', default=None)
@click.option('--sleep-after-upgrade', envvar='CRANE_SLEEP_AFTER_UPGRADE', default=None)
@click.option('--no-finish-upgrade', envvar='CRANE_NO_FINISH_UPGRADE', default=False, is_flag=True)
def main(rancher_url, access, secret, project, stack, service, new_image, batch_size, batch_interval, start_first, sidekick,
         sleep_after_upgrade, no_finish_upgrade):

    log = glog.bind(project=project, service=service, new_image=new_image, sidekick=sidekick)

    stack, service = ids.names_to_ids(rancher_url, project, stack, service, access, secret)

    launch_config, secondary_launch_config = utils.get_launch_configs(
        rancher_url, project, service, sidekick, new_image, access, secret
    )
    upgrade_request = utils.get_upgrade_request(
        batch_size, batch_interval, start_first, launch_config, secondary_launch_config
    )

    utils.upgrade(
        rancher_url, project, service, upgrade_request, sleep_after_upgrade, no_finish_upgrade, log, access, secret
    )

if __name__ == '__main__':
    main()
