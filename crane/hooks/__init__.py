from . import echo, slack

AVAILABLE_HOOKS = [echo, slack]

HOOKS = []

def dispatch(event):
    if not HOOKS:
        HOOKS.extend(getattr(module, 'Hook')() for module in AVAILABLE_HOOKS)

    for hook in HOOKS:
        hook.dispatch(event)
