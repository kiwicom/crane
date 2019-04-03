import os
import sys

import click

from .rancher import Deployment
from . import hooks, settings
from .exc import UpgradeFailed


def strip_trailing_slash(_, param, value):
    if not value:
        return

    return (
        value.rstrip("/")
        if not param.multiple
        else tuple(url.rstrip("/") for url in value)
    )


# Ignore PyCommentedCodeBear
# fmt: off
# start ignoring LineLengthBear
@click.command()
@click.option('--url', envvar='RANCHER_URL', required=True, help='Rancher API URL', callback=strip_trailing_slash)
@click.option('--access-key', envvar='RANCHER_ACCESS_KEY', required=True, help='Rancher access key')
@click.option('--secret-key', envvar='RANCHER_SECRET_KEY', required=True, help='Rancher secret key')
@click.option('--env', envvar='RANCHER_ENV_ID', required=True, help='ID of environment to operate in')
@click.option('--stack', envvar='RANCHER_STACK_NAME', required=True, help='stack to upgrade')
@click.option('--service', envvar='RANCHER_SERVICE_NAME', default=['app'], multiple=True, help='services to upgrade', show_default=True)
@click.option('--sidekick', envvar='RANCHER_SIDEKICK_NAME', default=None, help='sidekick to use instead of primary service')
@click.option('--batch-size', envvar='CRANE_BATCH_SIZE', default=1, help='containers to upgrade at once', show_default=True)
@click.option('--batch-interval', envvar='CRANE_BATCH_INTERVAL', default=2, help='seconds to wait between batches', show_default=True)
@click.option('--start-first', envvar='CRANE_START_FIRST', default=False, is_flag=True, help='start new containers before stopping old')
@click.option('--new-commit', envvar='CRANE_NEW_COMMIT', default=lambda: os.getenv('CI_COMMIT_SHA'), help='commit hash to upgrade to')
@click.option('--new-image', envvar='CRANE_NEW_IMAGE', help='image URL to upgrade to')
@click.option('--sleep-after-upgrade', envvar='CRANE_SLEEP_AFTER_UPGRADE', default=0, help='seconds to wait after upgrade', show_default=True)
@click.option('--manual-finish', envvar='CRANE_MANUAL_FINISH', default=False, is_flag=True, help='skip automatic upgrade finish')
@click.option('--slack-token', envvar='CRANE_SLACK_TOKEN', default=None, help='Slack API token')
@click.option('--slack-channel', envvar='CRANE_SLACK_CHANNEL', default=None, multiple=True, help='Slack channel to announce in')
@click.option('--slack-link', envvar='CRANE_SLACK_LINK', multiple=True, type=(str, str), metavar='TITLE URL', help='links to mention in Slack')
@click.option('--sentry-webhook', envvar='CRANE_SENTRY_WEBHOOK', default=None, help='Sentry release webhook URL', callback=strip_trailing_slash)
@click.option('--webhook-url', envvar='CRANE_WEBHOOK_URL', default=None, multiple=True, help='URLs to POST the release status to', callback=strip_trailing_slash)
@click.option('--webhook-token', envvar='CRANE_WEBHOOK_TOKEN', default=None, help='auth token for webhooks')
@click.option('--datadog-key', envvar='CRANE_DATADOG_KEY', default=None, help='key for posting release events')
# stop ignoring LineLengthBear
# Ignore PyCommentedCodeBear
# fmt: on
def main(**parsed_settings):
    click_context = click.get_current_context()
    click_context.color = True  # GitLab doesn't report terminal type correctly so we need to force it

    settings.update(parsed_settings)

    deployment = Deployment()
    try:
        deployment.load_from_settings()
        deployment.check_preconditions()
    except UpgradeFailed:
        sys.exit(1)  # we handled it gracefully already

    hooks.dispatch('before_upgrade', deployment=deployment)

    try:
        deployment.upgrade()
    except Exception as ex:
        hooks.dispatch('after_upgrade_failure', deployment=deployment)
        if isinstance(ex, UpgradeFailed):
            sys.exit(1)  # we handled it gracefully already
        raise
    else:
        hooks.dispatch('after_upgrade_success', deployment=deployment)
