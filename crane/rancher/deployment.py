import time

import attr
import click
import pybreaker
import requests

from crane.exc import UpgradeFailed
from . import models
from .. import deployment, settings


@attr.s
class Deployment(deployment.Base):

    stack = attr.ib(default=None)
    services = attr.ib(default=None)

    def load_from_settings(self):
        super().load_from_settings()

        models.session.auth = settings["access_key"], settings["secret_key"]

        self.stack = models.Stack.from_name(settings["stack"])
        self.services = [
            self.stack.service_from_name(service) for service in settings["service"]
        ]

        old_image = self.services[0].json()["launchConfig"]["imageUuid"]

        if settings["new_image"]:
            self.old_version = old_image.split(":")[-1]
        else:
            self.old_version = self.get_sha_from_image(old_image)

    def check_preconditions(self):
        super().check_preconditions()

        for service in self.services:
            if (
                self.old_version not in service.json()["launchConfig"]["imageUuid"]
                and not settings["new_image"]
            ):
                click.secho(
                    "All selected services must have the same commit SHA. "
                    "Please manually change their versions so they are all the same, and then retry the upgrade.",
                    err=True,
                    fg="red",
                )
                raise UpgradeFailed()

    def start_upgrade(self):
        click.echo(f"Please supervise me at {self.stack.web_url}!")

        for service in self.services:
            service.start_upgrade(self.old_version, self.new_version)

    def wait_for_upgrade(self):
        upgraded_services = set()
        while upgraded_services != set(self.services):
            time.sleep(3)
            try:
                upgraded_services = set(self.get_upgraded_services(upgraded_services))
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

    def get_upgraded_services(self, already_upgraded):
        yield from already_upgraded

        for service in set(self.services) - already_upgraded:
            service_json = service.json()
            if service_json["state"] == "upgrading":
                continue

            yield service

            click.echo(
                f"Rancher says {service.log_name} is now '{service_json['state']}'."
            )
            if service_json["state"] != "upgraded":
                click.secho(
                    f"But I don't know what {service.log_name}'s '{service_json['state']}' state means! "
                    + "Please fix it for me "
                    + click.style("(´;︵;`)", bold=True),
                    fg="red",
                    err=True,
                )
                raise UpgradeFailed()

    def finish_upgrade(self):
        if settings["manual_finish"]:
            return

        for service in self.services:
            service.finish_upgrade()
