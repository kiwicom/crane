from . import echo, sentry, slack, webhook

AVAILABLE_HOOKS = [echo, sentry, slack, webhook]

HOOKS = []


def dispatch(event):
    if not HOOKS:
        HOOKS.extend(getattr(module, 'Hook')() for module in AVAILABLE_HOOKS)

    for hook in HOOKS:
        hook.dispatch(event)
