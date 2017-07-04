from os import environ
import sys

import click
import crane
import git

from . import deployment, hooks, rancher, settings


@click.command()
@click.option('--url', envvar='RANCHER_URL', required=True, help='Rancher API URL')
@click.option('--access-key', envvar='RANCHER_ACCESS_KEY', required=True, help='Rancher access key')
@click.option('--secret-key', envvar='RANCHER_SECRET_KEY', required=True, help='Rancher secret key')
@click.option('--env', envvar='RANCHER_ENV_ID', required=True, help='ID of environment to operate in')
@click.option('--stack', envvar='RANCHER_STACK_NAME', required=True, help='stack to upgrade')
@click.option('--service', envvar='RANCHER_SERVICE_NAME', default='app', multiple=True, help='services to upgrade', show_default=True)
@click.option('--sidekick', envvar='RANCHER_SIDEKICK_NAME', default=None, help='sidekick to use instead of primary service')
@click.option('--batch-size', envvar='CRANE_BATCH_SIZE', default=1, help='containers to upgrade at once', show_default=True)
@click.option('--batch-interval', envvar='CRANE_BATCH_INTERVAL', default=2, help='seconds to wait between batches', show_default=True)
@click.option('--start-first', envvar='CRANE_START_FIRST', default=False, is_flag=True, help='start new containers before stopping old')
@click.option('--new-image', envvar='CRANE_NEW_IMAGE', default=None, help='Docker image URL to upgrade to')
@click.option('--sleep-after-upgrade', envvar='CRANE_SLEEP_AFTER_UPGRADE', default=0, help='seconds to wait after upgrade', show_default=True)
@click.option('--manual-finish', envvar='CRANE_MANUAL_FINISH', default=False, is_flag=True, help='skip automatic upgrade finish')
@click.option('--slack-token', envvar='CRANE_SLACK_TOKEN', default=None, help='Slack API token')
@click.option('--slack-channel', envvar='CRANE_SLACK_CHANNEL', default=None, help='Slack channel to announce in')
def main(**parsed_settings):
    click_context = click.get_current_context()
    click_context.color = True  # GitLab doesn't report terminal type correctly so we need to force it

    settings.update(parsed_settings)
    rancher.session.auth = settings['access_key'], settings['secret_key']
    deployment.load_from_settings(settings)

    hooks.dispatch('before_upgrade')

    try:
        for service in deployment.services:
            service.upgrade()
    except Exception as ex:
        hooks.dispatch('after_upgrade_failure')
        if isinstance(ex, rancher.UpgradeFailed):
            return  # we handled it gracefully already
        raise
    else:
        hooks.dispatch('after_upgrade_success')
