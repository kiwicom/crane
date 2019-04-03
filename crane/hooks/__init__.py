import traceback

import click

from . import datadog, echo, sentry, slack, webhook

AVAILABLE_HOOKS = [datadog, echo, sentry, slack, webhook]

HOOKS = []


def dispatch(event, *, deployment):
    if deployment.is_limited:
        return

    if not HOOKS:
        for module in AVAILABLE_HOOKS:
            hook_class = getattr(module, "Hook")
            try:
                HOOKS.append(hook_class(deployment))
            except:
                click.secho(
                    f"Oh, this is bad. I cannot load the '{module}' hook! "
                    + "Even if you weren't planning to use it, this should never happen. "
                    + "Please tell the maintainers about this at https://github.com/kiwicom/crane/issues/new "
                    + "— sorry about all the trouble!"
                    + click.style("(シ_ _)シ", bold=True),
                    fg="red",
                    err=True,
                )
                click.secho("Here's the traceback:\n", fg="red", err=True)
                traceback.print_exc()

    for hook in HOOKS:
        hook.dispatch(event)
