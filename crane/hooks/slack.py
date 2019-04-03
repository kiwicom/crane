from collections import UserList
import json
from os import environ

import backoff
import click
import requests

from .. import settings
from .base import Base

session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=5, pool_maxsize=5, max_retries=3
)
session.mount("http://", _adapter)
session.mount("https://", _adapter)


class AttachmentFields(UserList):
    """List subclass for working with Slack message attachment like dicts.

    So when you have fields like this::

        fields = [
            {'title': 'foo', 'value': 1, 'short': True},
            {'title': 'bar', 'value': 2, 'short': True},
        ]

    With this class you can::

        fields['foo'] = fields['bar'] * 10

    And the list will be edited to::

        fields = [
            {'title': 'foo', 'value': 20, 'short': True},
            {'title': 'bar', 'value': 2, 'short': True},
        ]
    """

    def __getitem__(self, item):
        for field in self.data:
            if field["title"] == item:
                return field["value"]
        else:
            raise KeyError(f"'{item}' is not one of the fields")

    def __setitem__(self, item, value):
        for field in self.data:
            if field["title"] == item:
                field["value"] = value
                return
        else:
            self.data.append({"title": item, "value": value, "short": True})

    @classmethod
    def aslist(cls, obj):
        if isinstance(obj, cls):
            return obj.data
        raise TypeError()


class Hook(Base):
    def __init__(self, deployment):
        super().__init__(deployment)
        self.token = settings["slack_token"]
        self.slack_channels = settings["slack_channel"]
        # The upcoming line is the most ridiculous, stupid, and effective hack I've ever written.
        # We create a link that has only a space as its link text, so it doesn't show up in Slack.
        # This allows us to store data in a fake URL, instead of needing a database or something.
        # Ridiculous.
        self.deployment_text = f"<{self.deployment.id}.com| >"

        self.users_by_email = {}
        self.channels_by_name = {}
        self.channel_ids = []

        if self.token and self.slack_channels:
            self.load_workspace_data()
            self.channel_ids = [
                self.channels_by_name[channel] for channel in self.slack_channels
            ]

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def load_workspace_data(self):
        users_response = session.get(
            "https://slack.com/api/users.list", params={"token": self.token}
        )
        users_response.raise_for_status()
        for user in users_response.json()["members"]:
            self.users_by_email[user["profile"].get("email")] = f"<@{user['id']}>"

        channels_response = session.get(
            "https://slack.com/api/channels.list", params={"token": self.token}
        )
        channels_response.raise_for_status()
        for channel in channels_response.json()["channels"]:
            self.channels_by_name[channel["name"]] = channel["id"]

    def base_data(self, channel_id):
        return {"token": self.token, "channel": channel_id}

    def get_existing_message(self, channel_id):
        response = session.get(
            "https://slack.com/api/channels.history", params=self.base_data(channel_id)
        )
        messages = response.json()["messages"]
        for message in messages:
            if message.get("text") == self.deployment_text:
                message["attachments"][0]["fields"] = AttachmentFields(
                    message["attachments"][0]["fields"]
                )
                return message

    def get_existing_messages(self):
        return {
            channel_id: self.get_existing_message(channel_id)
            for channel_id in self.channel_ids
        }

    @staticmethod
    def generate_cc_message(commit_msg):
        result = ",".join(
            line for line in commit_msg.splitlines() if line.lower().startswith("cc")
        )
        if result:
            result = ", " + result
        return result

    def get_changelog(self):
        if self.deployment.is_redeploy:
            return "Re-deploy without changes."

        prefix = ""
        if self.deployment.is_disconnected:
            prefix = (
                ":warning: The exact changes can't be determined from git history. "
                "The latest commit now is:\n"
            )
        elif self.deployment.is_rollback:
            prefix = ":warning: Rolling back the following changes:\n"

        return prefix + "\n".join(
            (
                f'<{environ["CI_PROJECT_URL"]}/commit/{commit.hexsha}|{commit.summary}> '
                f"by {self.users_by_email.get(commit.author.email, commit.author.name)}"
                f"{self.generate_cc_message(commit.message)}"
            )
            for commit in self.deployment.commits
            if len(commit.parents) == 1  # skip Merge commit
        )

    def generate_new_message(self):
        fields = AttachmentFields()
        # setting empty fields to keep them in consistent order
        fields["Environment"] = ""
        fields["Branch"] = ""
        fields["Releaser"] = ""
        fields["Links"] = self.links_text

        return {
            "link_names": True,
            "text": self.deployment_text,
            "attachments": [
                {
                    "fallback": f'{environ["CI_PROJECT_PATH"]} release',
                    "title": f'{environ["CI_PROJECT_PATH"]} release',
                    "title_link": f'{environ["CI_PROJECT_URL"]}/builds/{environ["CI_JOB_ID"]}',
                    "text": self.get_changelog(),
                    "fields": fields,
                }
            ],
        }

    def send_message(self, channel_id, message):
        fields = message["attachments"][0]["fields"]

        if ":x:" in fields["Environment"]:
            message["attachments"][0]["color"] = "danger"
        elif ":spinner:" in fields["Environment"]:
            message["attachments"][0].pop("color", None)
        else:
            message["attachments"][0]["color"] = "good"

        message["attachments"] = json.dumps(
            message["attachments"], default=AttachmentFields.aslist
        )
        if "ts" in message:
            url = "https://slack.com/api/chat.update"
            message["parse"] = True
        else:
            url = "https://slack.com/api/chat.postMessage"
        session.post(
            url, data={**self.base_data(channel_id), **message, "link_names": "1"}
        )

    def send_reply(self, channel_id, message_id, text, in_channel=False):
        session.post(
            "https://slack.com/api/chat.postMessage",
            data={
                **self.base_data(channel_id),
                "thread_ts": message_id,
                "text": text,
                "reply_broadcast": "true" if in_channel else "false",
                "link_names": "1",
            },
        )

    def set_status(self, message, status):
        fields = message["attachments"][0]["fields"]
        env_lines = fields["Environment"].splitlines()
        self.generate_env_lines(env_lines, status)
        fields["Environment"] = "\n".join(env_lines)

    def generate_env_lines(self, env_lines, status):
        for index, line in enumerate(env_lines):
            env_dict = {"status": "", "name": ""}
            words = line.split()
            if len(words) == 2:
                env_dict["status"] = words[0]
            env_dict["name"] = line.replace(env_dict["status"], "").strip()
            if env_dict["name"] == self.env_text:
                env_lines[index] = status + " " + self.env_text
                break
        else:
            env_lines.append(status + " " + self.env_text)

    def before_upgrade(self):
        messages = self.get_existing_messages() or {
            channel_id: self.generate_new_message() for channel_id in self.channel_ids
        }

        for channel_id, message in messages.items():
            fields = message["attachments"][0]["fields"]

            if "ts" in message:
                self.send_reply(
                    channel_id, message["ts"], f"Starting release on {self.env_text}."
                )

            self.set_status(message, ":spinner:")

            releaser = self.users_by_email.get(
                environ["GITLAB_USER_EMAIL"], environ["GITLAB_USER_EMAIL"]
            )
            if fields["Releaser"] and releaser.strip("@") not in fields["Releaser"]:
                fields["Releaser"] += " & " + releaser
            else:
                fields["Releaser"] = releaser

            fields["Branch"] = (
                (":warning: " if environ["CI_COMMIT_REF_NAME"] != "master" else "")
                + f'<{environ["CI_PROJECT_URL"]}/tree/{environ["CI_COMMIT_REF_NAME"]}|{environ["CI_COMMIT_REF_NAME"]}>'
            )

            self.send_message(channel_id, message)

    def after_upgrade_success(self):
        messages = self.get_existing_messages()
        if not messages:
            return  # we didn't even start
        for channel_id, message in messages.items():
            self.set_status(message, ":white_check_mark:")
            self.send_message(channel_id, message)
            self.send_reply(channel_id, message["ts"], f"Released on {self.env_text}.")

    def after_upgrade_failure(self):
        messages = self.get_existing_messages()
        if not messages:
            return  # we didn't even start
        for channel_id, message in messages.items():
            self.set_status(message, ":x:")
            self.send_message(channel_id, message)
            self.send_reply(
                channel_id,
                message["ts"],
                f"Release failed on {self.env_text}.",
                in_channel=True,
            )

    @property
    def is_active(self):
        provided = missing = None
        if self.token and not self.slack_channels:
            provided, missing = "API token", "channel"
        elif self.slack_channels and not self.token:
            provided, missing = "channel", "API token"

        if missing:
            click.secho(
                f"You have set a Slack {provided}, but forgot about setting the {missing}! "
                "We all make mistakes though, don't worry "
                + click.style("(⊃｡•́‿•̀｡)⊃", bold=True),
                err=False,
                fg="yellow",
            )

        return self.token and self.slack_channels

    @property
    def env_text(self):
        if "CI_ENVIRONMENT_URL" in environ:
            return f'<{environ["CI_ENVIRONMENT_URL"]}|{environ["CI_ENVIRONMENT_NAME"]}>'
        else:
            return environ["CI_ENVIRONMENT_NAME"]

    @property
    def links_text(self):
        links = {
            "Image": f'{environ["CI_REGISTRY_IMAGE"]}:{self.deployment.new_version}',
            **dict(settings["slack_link"]),
        }

        try:
            links["Stack"] = self.deployment.stack.web_url
        except AttributeError:
            pass

        return " | ".join(f"<{url}|{title}>" for title, url in links.items())
