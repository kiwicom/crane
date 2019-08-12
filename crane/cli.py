import sys

import click

from .deployment import Base as BaseDeployment
from .rancher import Deployment as RancherDeployment
from . import hooks, options
from .exc import UpgradeFailed


@click.group()
@click.pass_context
def cli(ctx, **kwargs):
    ctx.color = (
        True
    )  # GitLab doesn't report terminal type correctly so we need to force it

    ctx.obj = BaseDeployment.from_context(ctx)


@cli.command()
@click.argument(
    "event",
    nargs=1,
    type=click.Choice(["start", "success", "failure"]),
    metavar="EVENT",
)
@click.pass_obj
def announce(deployment, event, **kwargs):
    hooks.dispatch(event, deployment=deployment)


@cli.command()
@click.argument("target", nargs=1, type=click.Choice(["rancher1"]), metavar="TARGET")
@click.pass_context
def deploy(ctx, target, **kwargs):
    if ctx.params.get("new_commit") and ctx.params.get("new_image"):
        click.secho(
            "Please set only --new-commit or only --new-image. "
            "It doesn't make sense to set both, now does it?",
            fg="red",
            err=True,
        )
        sys.exit(2)

    if not ctx.params.get("new_commit") and not ctx.params.get("new_image"):
        click.secho(
            "Please set --new-commit or --new-image. "
            "I can't do much if I don't know what to upgrade to.",
            fg="red",
            err=True,
        )
        sys.exit(2)

    try:
        deployment = ctx.obj = RancherDeployment.from_context(ctx)
        deployment.check_preconditions()
    except UpgradeFailed:
        sys.exit(1)  # we handled it gracefully already

    hooks.dispatch("start", deployment=deployment)

    try:
        deployment.upgrade()
    except Exception as ex:
        hooks.dispatch("failure", deployment=deployment)
        if isinstance(ex, UpgradeFailed):
            sys.exit(1)  # we handled it gracefully already
        raise
    else:
        hooks.dispatch("success", deployment=deployment)


cli.params += options.FOR_HOOKS
deploy.params += [*options.FOR_DEPLOYS, *options.FOR_RANCHER]
