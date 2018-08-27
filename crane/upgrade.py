import time

import click
import pybreaker
import requests

from . import settings, deployment
from .exc import UpgradeFailed


def upgrade(services):
    click.echo("Alrighty, let's deploy! " + click.style("ᕕ( ᐛ )ᕗ", bold=True))
    click.echo(f"(But please supervise me at {deployment.stack.web_url})")

    service_start_upgrade(services)
    wait_for_upgrade(services)
    after_upgrade(services)


def after_upgrade(services):
    if settings["sleep_after_upgrade"]:
        click.echo(
            f'Upgrade done, waiting {settings["sleep_after_upgrade"]}s as requested '
            + click.style("(ʃƪ˘･ᴗ･˘)", bold=True)
        )
        time.sleep(settings["sleep_after_upgrade"])
    if not settings["manual_finish"]:
        service_finish_upgrade(services)


def wait_for_upgrade(services):
    done = set()
    while done != set(services):
        time.sleep(3)
        try:
            check_state(services, done)
        except requests.RequestException:
            continue
        except pybreaker.CircuitBreakerError:
            click.secho(
                "Rancher is unreachable! Please fix it for me "
                + click.style("(´･ω･`)", bold=True),
                fg="red",
                err=True,
            )
            raise UpgradeFailed()


def service_start_upgrade(services):
    for service in services:
        service.start_upgrade()


def service_finish_upgrade(services):
    for service in services:
        service.finish_upgrade()


def check_state(services, done):
    for service in set(services) - done:
        service_json = service.json()

        if service_json["state"] != "upgrading":
            click.echo(
                f"Rancher says {service.log_name} is now '{service_json['state']}'."
            )
            done.add(service)
            if service_json["state"] != "upgraded":
                click.secho(
                    f"But I don't know what {service.log_name}'s '{service_json['state']}' state means! "
                    + "Please fix it for me "
                    + click.style("(´;︵;`)", bold=True),
                    fg="red",
                    err=True,
                )
                raise UpgradeFailed()
