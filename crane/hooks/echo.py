import click

from .. import deployment
from .base import Base


class Hook(Base):

    is_active = True

    def before_upgrade(self):
        click.echo("Alrighty, let's deploy! " + click.style('ᕕ( ᐛ )ᕗ', bold=True))
        click.echo(f'(But please supervise me at {deployment.stack.web_url})')

    def after_upgrade_success(self):
        click.secho("…and we're done. Good job, everyone! " + click.style('(◕‿◕✿)', bold=True), fg='green')

    def after_upgrade_failure(self):
        click.echo()  # add newline before the traceback
