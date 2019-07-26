import traceback

import click


class Base:

    is_active = False

    def __init__(self, deployment):
        self.deployment = deployment

    @property
    def ctx(self):
        return self.deployment.ctx

    def start(self):
        return

    def success(self):
        return

    def failure(self):
        return

    def dispatch(self, event):
        if not self.is_active:
            return

        handler = getattr(self, event)
        try:
            handler()
        except:
            click.secho(
                f"Uh-oh, {self.__module__} couldn't handle {event}. Here's the traceback:\n",
                fg="yellow",
                err=True,
            )
            traceback.print_exc()
            click.echo(
                "\nOh well, on with the release! " + click.style("乁( ◔ ౪◔)ㄏ", bold=True)
            )
