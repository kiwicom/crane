from . import echo, sentry, slack

AVAILABLE_HOOKS = [echo, sentry, slack]

HOOKS = []

def dispatch(event):
    if not HOOKS:
        HOOKS.extend(getattr(module, 'Hook')() for module in AVAILABLE_HOOKS)

    for hook in HOOKS:
        hook.dispatch(event)
