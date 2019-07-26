import types

import pytest
import datadog
from crane.hooks import datadog as uut
from crane import deployment


@pytest.fixture
def ctx():
    ctx = types.SimpleNamespace()
    ctx.params = {"datadog_key": "here da key"}
    return ctx


@pytest.mark.parametrize(
    ["commits", "event", "text"],
    [
        [["1"], "success", "1"],
        [["1", "2"], "success", "1\n2"],
        [[], "success", ""],
        [["1"], "error", "1"],
    ],
)
def test_create_event(monkeypatch, mocker, repo, ctx, commits, event, text):
    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit)

    tags = ["releaser:picky@kiwi.com", "project:foo/bar", "environment:a-b/c-d"]

    fake_create = mocker.patch.object(datadog.api.Event, "create")
    fake_deployment = deployment.Base(
        ctx=ctx, repo=repo, new_version="HEAD", old_version=old_version
    )

    dd_hook = uut.Hook(fake_deployment)
    if event == "success":
        dd_hook.success()
    elif event == "error":
        dd_hook.failure()

    fake_create.assert_called_with(
        title="foo/bar deployment", text=text, tags=tags, alert_type=event
    )