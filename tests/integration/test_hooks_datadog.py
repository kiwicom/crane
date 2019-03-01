import pytest
import datadog
from crane.hooks import datadog as uut
from crane import deployment


@pytest.mark.parametrize(
    ["commits", "event", "text"],
    [
        [["1"], "success", "1"],
        [["1", "2"], "success", "1\n2"],
        [[], "success", ""],
        [["1"], "error", "1"],
    ],
)
def test_create_event(monkeypatch, mocker, repo, commits, event, text):
    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit)

    tags = ["releaser:picky@kiwi.com", "project:foo/bar", "environment:a-b/c-d"]

    fake_create = mocker.patch.object(datadog.api.Event, "create")
    fake_deployment = deployment.Base(
        repo=repo, new_version="HEAD", old_version=old_version
    )

    dd_hook = uut.Hook(fake_deployment)
    if event == "success":
        dd_hook.after_upgrade_success()
    elif event == "error":
        dd_hook.after_upgrade_failure()

    fake_create.assert_called_with(
        title="foo/bar deployment", text=text, tags=tags, alert_type=event
    )
