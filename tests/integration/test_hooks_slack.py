import re

import pytest
import requests
from datetime import datetime
from git import Actor

from crane.hooks import slack as uut
from crane import settings, deployment
from crane.hooks.slack import AttachmentFields
from crane import rancher
from crane.rancher import models as rancher_models


@pytest.fixture(autouse=True)
def click_settings(monkeypatch):
    monkeypatch.setitem(settings, "slack_token", "xoxp-123-456")
    monkeypatch.setitem(settings, "slack_channel", ["general", "team"])
    monkeypatch.setitem(settings, "slack_link", "")
    monkeypatch.setitem(settings, "url", "asd")
    monkeypatch.setitem(settings, "env", "asd")
    monkeypatch.setitem(settings, "stack", "asd")


@pytest.fixture(autouse=True)
def mock_slack_api(requests_mock):
    requests_mock.get(
        "https://slack.com/api/users.list",
        json={"members": [{"profile": {"email": "jd@kiwi.com"}, "id": "123"}]},
    )
    requests_mock.get(
        "https://slack.com/api/channels.list",
        json={
            "channels": [{"name": "general", "id": "123"}, {"name": "team", "id": "42"}]
        },
    )


@pytest.mark.parametrize(["slack_response", "result"], [[{"messages": []}, None]])
def test_get_existing_message(monkeypatch, mocker, repo, slack_response, result):
    old_version = repo.head.commit.hexsha
    for commit in ["1"]:
        repo.index.commit(commit, author=Actor("test_author", "test@test.com"))

    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )
    slack_hook = uut.Hook(fake_deployment)
    slack_hook.channel_ids = ["123"]
    fake_get = mocker.patch.object(uut.session, "get")
    fake_response = mocker.Mock()
    fake_response.json = lambda: {"messages": []}
    fake_get.return_value = fake_response

    assert slack_hook.get_existing_message("123") is None

    deployment_id = f"<{slack_hook.deployment.id}.com| >"

    fake_response.json = lambda: {
        "messages": [
            {"text": deployment_id, "attachments": [{"fields": []}]},
            {"text": "colemak", "attachments": [{"fields": []}]},
        ]
    }
    assert slack_hook.get_existing_message("123")["text"] == deployment_id
    assert slack_hook.get_existing_message("123")["attachments"][0][
        "fields"
    ] == uut.AttachmentFields([])


@pytest.mark.parametrize(["slack_response", "result"], [[{"messages": []}, None]])
def test_get_existing_messages(monkeypatch, mocker, repo, slack_response, result):
    old_version = repo.head.commit.hexsha
    for commit in ["1"]:
        repo.index.commit(commit, author=Actor("test_author", "test@test.com"))

    fake_deployment = Deployment(repo=repo, new_version="HEAD", old_version=old_version)
    monkeypatch.setattr(uut, "deployment", fake_deployment)
    slack_hook = uut.Hook()
    slack_hook.channel_ids = ["123", "asd"]
    fake_get = mocker.patch.object(uut.session, "get")
    fake_response = mocker.Mock()
    fake_response.json = lambda: {"messages": []}
    fake_get.return_value = fake_response

    assert slack_hook.get_existing_messages() == {"123": None, "asd": None}

    deployment_id = f"<{uut.deployment.id}.com| >"

    fake_response.json = lambda: {
        "messages": [
            {"text": deployment_id, "attachments": [{"fields": []}]},
            {"text": "colemak", "attachments": [{"fields": []}]},
        ]
    }
    messages = slack_hook.get_existing_messages()
    assert len(messages) == 2
    assert messages["123"]["text"] == deployment_id
    assert messages["asd"]["attachments"][0]["fields"] == uut.AttachmentFields([])


@pytest.mark.parametrize(
    ["commits", "expected"],
    [
        [[], ""],
        [
            ["1"],
            "<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|1> by test_author",
        ],
        [
            ["1", "2"],
            "<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|1> by test_author\n<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|2> by test_author",
        ],
        [
            ["1\ncc @picky cause reasons"],
            "<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|1> by test_author, cc @picky cause reasons",
        ],
        [
            ["1\nCC @picky cause reasons"],
            "<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|1> by test_author, CC @picky cause reasons",
        ],
    ],
)
def test_get_changelog(monkeypatch, repo, commits, expected):
    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit, author=Actor("test_author", "test@test.com"))

    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )

    slack_hook = uut.Hook(fake_deployment)
    slack_hook.users_by_email = {}

    changelog = slack_hook.get_changelog()
    assert re.fullmatch(expected, changelog)


@pytest.mark.parametrize(
    ["commits", "expected"],
    [
        [
            ["1"],
            ":warning: The exact changes can't be determined from git history. The latest commit now is:\n<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|1> by test_author",
        ],
        [
            ["1", "2"],
            ":warning: The exact changes can't be determined from git history. The latest commit now is:\n<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|2> by test_author",
        ],
        [
            ["1\ncc @picky cause reasons"],
            ":warning: The exact changes can't be determined from git history. The latest commit now is:\n<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|1> by test_author, cc @picky cause reasons",
        ],
        [
            ["1\nCC @picky cause reasons"],
            ":warning: The exact changes can't be determined from git history. The latest commit now is:\n<https://example.com/foo/bar/commit/[A-Fa-f0-9]{40}\|1> by test_author, CC @picky cause reasons",
        ],
    ],
)
def test_get_changelog_force_push(monkeypatch, repo, commits, expected):
    old_version = "0000000000000000000000000000000000000000"
    for commit in commits:
        repo.index.commit(commit, author=Actor("test_author", "test@test.com"))

    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )

    slack_hook = uut.Hook(fake_deployment)
    slack_hook.users_by_email = {}

    changelog = slack_hook.get_changelog()
    assert re.fullmatch(expected, changelog)


def test_get_changelog_redeploy(monkeypatch, repo):
    fake_deployment = deployment.Base(repo=repo, new_version="HEAD", old_version="HEAD")
    slack_hook = uut.Hook(fake_deployment)
    slack_hook.users_by_email = {}
    assert fake_deployment.is_redeploy, "deployment should be redeploy"
    assert slack_hook.get_changelog() == "Re-deploy without changes."


def test_get_changelog_rollback(monkeypatch, repo):
    ts = datetime(2017, 1, 1, 0, 0, 0).isoformat()
    old_version = repo.head.commit.hexsha
    for commit in ["1"]:
        repo.index.commit(
            commit, author=Actor("test_author", "test@test.com"), commit_date=ts
        )

    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )
    slack_hook = uut.Hook(fake_deployment)
    slack_hook.users_by_email = {}

    changelog = slack_hook.get_changelog()

    assert fake_deployment.is_rollback, "deployment should be rollback"
    assert changelog.startswith(
        ":warning: Rolling back the following changes:\n"
    ), "rollback didn't display correct changelog"


@pytest.mark.parametrize(
    ["commits", "expected"],
    [
        [
            ["1"],
            {
                "link_names": True,
                "text": "",
                "attachments": [
                    {
                        "fallback": "foo/bar release",
                        "title": "foo/bar release",
                        "title_link": "https://example.com/foo/bar/builds/1234567",
                        "text": "",
                        "fields": [
                            {"title": "Environment", "value": "", "short": True},
                            {"title": "Branch", "value": "", "short": True},
                            {"title": "Releaser", "value": "", "short": True},
                            {
                                "title": "Links",
                                "value": "<registry.example.com/foo/bar:HEAD|Image> | <asd/env/asd/apps/stacks/0st0|Stack>",
                                "short": True,
                            },
                        ],
                    }
                ],
            },
        ]
    ],
)
def test_generate_new_message(monkeypatch, repo, commits, expected):
    monkeypatch.setenv("CI_ENVIRONMENT_URL", "example.com")

    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit, author=Actor("test_author", "test@test.com"))

    fake_deployment = rancher.Deployment(
        repo=repo,
        new_version="HEAD",
        old_version=old_version,
        stack=rancher_models.Stack("0st0", "foo"),
    )

    slack_hook = uut.Hook(fake_deployment)
    slack_hook.get_changelog = lambda: ""
    slack_hook.users_by_email = {"picky@kiwi.com": "@picky"}

    msg = slack_hook.generate_new_message()
    expected["text"] = slack_hook.deployment_text
    assert msg == expected


@pytest.mark.parametrize(
    ["message_title", "url", "result_message"],
    [
        [
            {"title": "Environment", "value": "", "short": True},
            "https://slack.com/api/chat.postMessage",
            '[{"fields": [{"title": "Environment", "value": "", "short": true}], "color": "good"}]',
        ],
        [
            {"title": "Environment", "value": ":foo:", "short": True},
            "https://slack.com/api/chat.postMessage",
            '[{"fields": [{"title": "Environment", "value": ":foo:", "short": true}], "color": "good"}]',
        ],
        [
            {"title": "Environment", "value": ":x:", "short": True},
            "https://slack.com/api/chat.postMessage",
            '[{"fields": [{"title": "Environment", "value": ":x:", "short": true}], "color": "danger"}]',
        ],
        [
            {"title": "Environment", "value": ":x: foo", "short": True},
            "https://slack.com/api/chat.postMessage",
            '[{"fields": [{"title": "Environment", "value": ":x: foo", "short": true}], "color": "danger"}]',
        ],
        [
            {"title": "Environment", "value": ":spinner:", "short": True},
            "https://slack.com/api/chat.postMessage",
            '[{"fields": [{"title": "Environment", "value": ":spinner:", "short": true}]}]',
        ],
    ],
)
def test_send_message(monkeypatch, mocker, repo, message_title, url, result_message):
    old_version = repo.head.commit.hexsha
    repo.index.commit("1")

    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )
    fake_post = mocker.patch.object(requests.Session, "post")

    slack_hook = uut.Hook(fake_deployment)
    slack_hook.channel_ids = ["asd"]
    slack_hook.send_message(
        "asd", {"attachments": [{"fields": AttachmentFields([message_title])}]}
    )
    base_data = {"token": "xoxp-123-456", "channel": "asd"}
    fake_post.assert_called_with(
        url, data={**base_data, "attachments": result_message, "link_names": "1"}
    )


@pytest.mark.parametrize(["message_id", "text"], [["aa", "1"]])
def test_send_reply(monkeypatch, mocker, repo, message_id, text):
    old_version = repo.head.commit.hexsha
    for commit in ["4"]:
        repo.index.commit(commit)

    fake_post = mocker.patch.object(requests.Session, "post")
    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )

    slack_hook = uut.Hook(fake_deployment)
    slack_hook.channel_ids = ["asd"]
    slack_hook.send_reply(message_id, text)

    fake_post.assert_called_with(
        "https://slack.com/api/chat.postMessage",
        data={
            "token": "xoxp-123-456",
            "channel": "asd",
            "thread_ts": message_id,
            "text": text,
            "reply_broadcast": "false",
            "link_names": "1",
        },
    )


@pytest.mark.parametrize(
    ["environment_before", "environment_after", "expected"],
    [
        ["", ":abc:", ":abc: a-b/c-d"],
        [":aaa: a-b/c-d", ":abc:", ":abc: a-b/c-d"],
        [":abc: foo/bar\n:aaa: a-b/c-d", ":abc:", ":abc: foo/bar\n:abc: a-b/c-d"],
    ],
)
def test_set_status(monkeypatch, repo, environment_before, environment_after, expected):
    old_version = repo.head.commit.hexsha
    for commit in ["1"]:
        repo.index.commit(commit)

    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )
    message = {"attachments": [{"fields": {"Environment": environment_before}}]}

    slack_hook = uut.Hook(fake_deployment)
    slack_hook.channel_ids = ["asd"]
    slack_hook.set_status(message, environment_after)

    assert message["attachments"][0]["fields"]["Environment"] == expected


def test_is_active__active(repo):
    fake_deployment = deployment.Base(repo=repo, new_version="HEAD", old_version="HEAD")
    slack_hook = uut.Hook(fake_deployment)
    assert slack_hook.is_active


@pytest.mark.parametrize(
    ["missing_setting", "expected_error"],
    [
        ("slack_token", "forgot about setting the API token"),
        ("slack_channel", "forgot about setting the channels"),
    ],
)
def test_is_active__missing_one(
    repo, missing_setting, expected_error, monkeypatch, mocker
):
    monkeypatch.setitem(settings, missing_setting, None)
    mock_secho = mocker.patch.object(uut.click, "secho")

    fake_deployment = deployment.Base(repo=repo, new_version="HEAD", old_version="HEAD")
    slack_hook = uut.Hook(fake_deployment)
    assert not slack_hook.is_active
    assert any([expected_error in str(args[0]) for args in mock_secho.call_args_list])


def test_is_active__inactive(monkeypatch, repo):
    monkeypatch.setitem(settings, "slack_token", None)
    monkeypatch.setitem(settings, "slack_channel", None)

    fake_deployment = deployment.Base(repo=repo, new_version="HEAD", old_version="HEAD")
    slack_hook = uut.Hook(fake_deployment)
    assert not slack_hook.is_active
