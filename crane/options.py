import os

from click import Option


def strip_trailing_slash(_, param, value):
    if not value:
        return

    return (
        value.rstrip("/")
        if not param.multiple
        else tuple(url.rstrip("/") for url in value)
    )


FOR_HOOKS = [
    Option(
        ["--slack-token"],
        envvar="CRANE_SLACK_TOKEN",
        default=None,
        help="Slack API token",
    ),
    Option(
        ["--slack-channel"],
        envvar="CRANE_SLACK_CHANNEL",
        default=None,
        multiple=True,
        help="Slack channel to announce in",
    ),
    Option(
        ["--slack-link"],
        envvar="CRANE_SLACK_LINK",
        multiple=True,
        type=(str, str),
        metavar="TITLE URL",
        help="links to mention in Slack",
    ),
    Option(
        ["--sentry-webhook"],
        envvar="CRANE_SENTRY_WEBHOOK",
        default=None,
        help="Sentry release webhook URL",
        callback=strip_trailing_slash,
    ),
    Option(
        ["--webhook-url"],
        envvar="CRANE_WEBHOOK_URL",
        default=None,
        multiple=True,
        help="URLs to POST the release status to",
        callback=strip_trailing_slash,
    ),
    Option(
        ["--webhook-token"],
        envvar="CRANE_WEBHOOK_TOKEN",
        default=None,
        help="auth token for webhooks",
    ),
    Option(
        ["--datadog-key"],
        envvar="CRANE_DATADOG_KEY",
        default=None,
        help="key for posting release events",
    ),
]

FOR_DEPLOYS = [
    Option(
        ["--batch-size"],
        envvar="CRANE_BATCH_SIZE",
        default=1,
        help="containers to upgrade at once",
        show_default=True,
    ),
    Option(
        ["--batch-interval"],
        envvar="CRANE_BATCH_INTERVAL",
        default=2,
        help="seconds to wait between batches",
        show_default=True,
    ),
    Option(
        ["--start-first"],
        envvar="CRANE_START_FIRST",
        default=False,
        is_flag=True,
        help="start new containers before stopping old",
    ),
    Option(
        ["--old-commit"],
        envvar="CRANE_OLD_COMMIT",
        default=None,
        help="commit hash we are upgrading from",
    ),
    Option(
        ["--new-commit"],
        envvar="CRANE_NEW_COMMIT",
        default=lambda: os.getenv("CI_COMMIT_SHA"),
        help="commit hash to upgrade to",
    ),
    Option(["--new-image"], envvar="CRANE_NEW_IMAGE", help="image URL to upgrade to"),
    Option(
        ["--sleep-after-upgrade"],
        envvar="CRANE_SLEEP_AFTER_UPGRADE",
        default=0,
        help="seconds to wait after upgrade",
        show_default=True,
    ),
    Option(
        ["--manual-finish"],
        envvar="CRANE_MANUAL_FINISH",
        default=False,
        is_flag=True,
        help="skip automatic upgrade finish",
    ),
]


FOR_RANCHER = [
    Option(
        ["--url"],
        envvar="RANCHER_URL",
        required=True,
        help="Rancher API URL",
        callback=strip_trailing_slash,
    ),
    Option(
        ["--access-key"],
        envvar="RANCHER_ACCESS_KEY",
        required=True,
        help="Rancher access key",
    ),
    Option(
        ["--secret-key"],
        envvar="RANCHER_SECRET_KEY",
        required=True,
        help="Rancher secret key",
    ),
    Option(
        ["--env"],
        envvar="RANCHER_ENV_ID",
        required=True,
        help="ID of environment to operate in",
    ),
    Option(
        ["--stack"],
        envvar="RANCHER_STACK_NAME",
        default=lambda: os.getenv("CI_PROJECT_NAME"),
        help="stack to upgrade",
    ),
    Option(
        ["--service"],
        envvar="RANCHER_SERVICE_NAME",
        default=["app"],
        multiple=True,
        help="services to upgrade",
        show_default=True,
    ),
    Option(
        ["--sidekick"],
        envvar="RANCHER_SIDEKICK_NAME",
        default=None,
        help="sidekick to use instead of primary service",
    ),
]
