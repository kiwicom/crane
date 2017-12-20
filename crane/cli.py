import time

import click
import git

import crane

from . import deployment, hooks, rancher, settings


# start ignoring LineLengthBear
@click.command()
@click.option('--rancher-url', '--url', envvar='RANCHER_URL', required=True, help='Rancher API URL')
@click.option('--access', '--access-key', envvar='RANCHER_ACCESS_KEY', required=True, help='Rancher access key')
@click.option('--secret', '--secret-key', envvar='RANCHER_SECRET_KEY', required=True, help='Rancher secret key')
@click.option('--project', '--env', envvar=['RANCHER_ENV_ID', 'RANCHER_PROJECT_ID'], required=True, help='ID of environment to operate in')
@click.option('--stack', envvar='RANCHER_STACK_NAME', required=True, help='stack to upgrade')
@click.option('--service', envvar=['RANCHER_SERVICE_NAME', 'RANCHER_SERVICE_ID'], default=['app'], multiple=True, help='services to upgrade', show_default=True)
@click.option('--sidekick', envvar='RANCHER_SIDEKICK_NAME', default=None, help='sidekick to use instead of primary service')
@click.option('--batch-size', envvar=['CRANE_BATCH_SIZE', 'RANCHER_BATCH_SIZE'], default=1, help='containers to upgrade at once', show_default=True)
@click.option('--batch-interval', envvar=['CRANE_BATCH_INTERVAL', 'RANCHER_BATCH_INTERVAL'], default=2, help='seconds to wait between batches', show_default=True)
@click.option('--start-first', envvar=['CRANE_START_FIRST', 'RANCHER_START_FIRST'], default=False, is_flag=True, help='start new containers before stopping old')
@click.option('--new-image', envvar=['CRANE_NEW_IMAGE', 'RANCHER_SERVICE_IMAGE'], required=True, help='URL of new Docker image, usually $CI_REGISTRY_IMAGE:$CI_BUILD_REF')
@click.option('--sleep-after-upgrade', envvar='CRANE_SLEEP_AFTER_UPGRADE', default=0, help='seconds to wait after upgrade', show_default=True)
@click.option('--no-finish-upgrade', '--manual-finish', envvar=['CRANE_MANUAL_FINISH', 'CRANE_NO_FINISH_UPGRADE'], default=False, is_flag=True, help='skip automatic upgrade finish')
@click.option('--slack-token', envvar='CRANE_SLACK_TOKEN', default=None, help='Slack API token')
@click.option('--slack-channel', envvar='CRANE_SLACK_CHANNEL', default=None, help='Slack channel to announce in')
@click.option('--slack-link', envvar='CRANE_SLACK_LINK', multiple=True, type=(str, str), metavar='TITLE URL', help='links to mention in Slack')
@click.option('--sentry-webhook', envvar='CRANE_SENTRY_WEBHOOK', default=None, help='Sentry release webhook URL')
@click.option('--webhook-url', envvar='CRANE_WEBHOOK_URL', default=None, multiple=True, help='URLs to POST the release status to')
@click.option('--webhook-token', envvar='CRANE_WEBHOOK_TOKEN', default=None, help='auth token for webhooks')
@click.option('--datadog-api-key', envvar='CRANE_DATADOG_API_KEY', default=None, help='key for posting release events')
# stop ignoring LineLengthBear
def main(**parsed_settings):
    click_context = click.get_current_context()
    click_context.color = True  # GitLab doesn't report terminal type correctly so we need to force it

    settings.update(parsed_settings)
    rancher.session.auth = settings['access_key'], settings['secret_key']
    deployment.load_from_settings(settings)

    hooks.dispatch('before_upgrade')

    try:
        upgrade()
    except Exception as ex:
        hooks.dispatch('after_upgrade_failure')
        if isinstance(ex, rancher.UpgradeFailed):
            return  # we handled it gracefully already
        raise
    else:
        hooks.dispatch('after_upgrade_success')


def upgrade():
    for service in deployment.services:
        service.start_upgrade()

    done = set()
    while done != set(deployment.services):
        time.sleep(3)
        for service in set(deployment.services) - done:
            service_json = service.json()
            if service_json['state'] != 'upgrading':
                click.echo(f"Rancher says {service.log_name} is now '{service_json['state']}'.")
                done.add(service)
                if service_json['state'] != 'upgraded':
                    click.secho(
                        f"But I don't know what {service.log_name}'s '{service_json['state']}' state means! "
                        + 'Please fix it for me ' + click.style('(´;︵;`)', bold=True),
                        fg='red',
                        err=True,
                    )
                    raise rancher.UpgradeFailed()

    if settings['sleep_after_upgrade']:
        click.echo(
            f'Upgrade done, waiting {settings["sleep_after_upgrade"]}s as requested '
            + click.style('(ʃƪ˘･ᴗ･˘)', bold=True)
        )
        time.sleep(settings['sleep_after_upgrade'])

    if not settings['manual_finish']:
        for service in deployment.services:
            service.finish_upgrade()
