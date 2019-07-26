import re

import attr
import click
import requests

import crane
import crane.exc
import pybreaker

session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=5, pool_maxsize=5, max_retries=3
)
session.mount("http://", _adapter)
session.mount("https://", _adapter)

time_breaker = pybreaker.CircuitBreaker(fail_max=20)


@attr.s(frozen=True, slots=True)
class Entity:

    rancher_url = attr.ib(validator=attr.validators.instance_of(str))
    env = attr.ib(validator=attr.validators.instance_of(str))
    id = attr.ib()
    name = attr.ib(validator=attr.validators.instance_of(str))

    @id.validator
    def validate_rancher_id(self, attribute, value):
        if not self.ID_PATTERN.match(value):
            raise ValueError("the Rancher ID seems incorrectly formatted")

    @property
    def log_name(self):
        return click.style(self.name, bold=True)

    @time_breaker
    def json(self):
        response = session.get(self.api_url, timeout=60)
        response.raise_for_status()
        return response.json()


@attr.s(frozen=True, slots=True)
class Stack(Entity):

    ID_PATTERN = re.compile("[0-9]st[0-9]+")

    @property
    def web_url(self):
        return f"{self.rancher_url}/env/{self.env}/apps/stacks/{self.id}"

    @property
    def api_url(self):
        return f"{self.rancher_url}/v1/projects/{self.env}/environments/{self.id}"

    @classmethod
    def from_name(cls, rancher_url, env, name):
        if not name:
            click.secho(
                f"Well, this is a bit awkward. You need to tell me what stack to upgrade in."
                + click.style("（˶′◡‵˶）", bold=True),
                err=True,
                fg="red",
            )
            click.secho(
                "Normally I can guess it from the CI environment, but it seems I'm not running in CI now.",
                err=True,
                fg="red",
            )
            raise crane.exc.UpgradeFailed()

        response = session.get(
            f"{rancher_url}/v1/projects/{env}/environments", params={"name": name}
        )
        response.raise_for_status()
        matches = response.json()["data"]

        if not matches:
            click.secho(
                f"I don't see a stack called '{name}' "
                + click.style("(・_・)ヾ", bold=True),
                err=True,
                fg="red",
            )
            click.secho(
                "I cannot upgrade like this, please check your configuration!",
                err=True,
                fg="red",
            )
            raise crane.exc.UpgradeFailed()

        return cls(
            rancher_url=rancher_url,
            env=env,
            id=matches[0]["id"].replace("1e", "1st"),
            name=matches[0]["name"],
        )

    def service_from_name(self, name):
        response = session.get(
            f"{self.rancher_url}/v1/projects/{self.env}/services",
            params={"name": name, "stackId": self.id},
        )
        response.raise_for_status()
        matches = response.json()["data"]
        if not matches:
            click.secho(
                f"I don't see a service called '{name}' in the '{self.name}' stack "
                + click.style("(・_・)ヾ", bold=True),
                err=True,
                fg="red",
            )
            click.secho(
                "I cannot upgrade like this, please check your configuration!",
                err=True,
                fg="red",
            )
            raise crane.exc.UpgradeFailed()
        return Service(
            rancher_url=self.rancher_url,
            env=self.env,
            id=matches[0]["id"],
            name=matches[0]["name"],
            stack=self,
        )


@attr.s(frozen=True, slots=True)
class Service(Entity):

    ID_PATTERN = re.compile("[0-9]s[0-9]+")
    stack = attr.ib(validator=attr.validators.instance_of(Stack))

    @property
    def web_url(self):
        return f"{self.stack.web_url}/services/{self.id}/containers"

    @property
    def api_url(self):
        return (
            f"{self.stack.rancher_url}/v1/projects/{self.stack.env}/services/{self.id}"
        )

    @property
    def launch_config(self):
        return self.json()["launchConfig"]

    @property
    def sidekick_launch_configs(self):
        return {
            config["name"]: config for config in self.json()["secondaryLaunchConfigs"]
        }

    def start_upgrade(self, old_version, new_version, cli_params):
        payload = {
            "inServiceStrategy": {
                "batchSize": cli_params["batch_size"],
                "intervalMillis": cli_params["batch_interval"] * 1000,
                "startFirst": cli_params["start_first"],
                "launchConfig": None,
                "secondaryLaunchConfigs": [],
            }
        }

        if not cli_params.get("rancher_sidekick"):
            launch_config = payload["inServiceStrategy"][
                "launchConfig"
            ] = self.launch_config
        else:
            launch_config = self.sidekick_launch_configs[cli_params["rancher_sidekick"]]
            payload["inServiceStrategy"]["secondaryLaunchConfigs"].append(launch_config)

        launch_config["imageUuid"] = (
            "docker:{new_image}".format_map(cli_params)
            if cli_params["new_image"]
            else launch_config["imageUuid"].replace(old_version, new_version)
        )

        click.echo(f"Upgrading {self.log_name}…")
        response = session.post(
            self.api_url, params={"action": "upgrade"}, json=payload, timeout=60
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            try:
                response_payload = ex.response.json()
            except:
                response_payload = None

            if (
                response_payload
                and response_payload.get("code") == "ActionNotAvailable"
            ):
                message = (
                    f"Rancher won't let me upgrade {self.log_name} "
                    + click.style("(◕︿◕✿)", bold=True)
                    + f"\n\nPlease see if the service is upgradeable at {self.web_url}"
                )
            else:
                message = (
                    f"Upgrade failed, and I don't know why "
                    + click.style("(◍•﹏•)", bold=True)
                    + f"\n\nHere, maybe you will understand this:\n{ex.response.text}"
                )

            click.secho(message, err=True, fg="red")

            raise crane.exc.UpgradeFailed()

    def finish_upgrade(self):
        response = session.post(
            self.api_url, params={"action": "finishupgrade"}, timeout=60, json={}
        )
        response.raise_for_status()
        click.echo(f"Marked upgrade of {self.log_name} as finished in Rancher.")
