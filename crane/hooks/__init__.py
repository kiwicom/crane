from . import datadog, echo, sentry, slack, webhook
from .. import deployment

AVAILABLE_HOOKS = [datadog, echo, sentry, slack, webhook]

HOOKS = []


def dispatch(event):
    if deployment.is_limited:
        return

    if not HOOKS:
        HOOKS.extend(getattr(module, "Hook")() for module in AVAILABLE_HOOKS)

    for hook in HOOKS:
        hook.dispatch(event)
