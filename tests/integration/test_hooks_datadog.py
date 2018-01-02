import git
import pytest
import tempfile
import datadog
from crane.hooks import datadog as uut
from crane import settings, Deployment


@pytest.fixture(autouse=True)
def click_settings(monkeypatch):
    monkeypatch.setitem(settings, 'datadog_api_key', '')
    monkeypatch.setitem(settings, 'datadog_app_key', '')


@pytest.fixture
def repo():
    with tempfile.TemporaryDirectory() as repo_dir:
        repo = git.Repo.init(repo_dir)
        repo.index.commit('Initial commit')
        yield repo


@pytest.mark.parametrize(['commits', 'event', 'text', 'tags'], [
    [['1'], 'success', '1', ['author:picky@kiwi.com', 'project:foo-bar']],
    [['1', '2'], 'success', '1\n2', ['author:picky@kiwi.com', 'project:foo-bar']],
    [[], 'success', '', ['author:picky@kiwi.com', 'project:foo-bar']],
    [['1'], 'failure', '1', ['author:picky@kiwi.com', 'project:foo-bar']],
])
def test_create_event(monkeypatch, mocker, repo, commits, event, text, tags):
    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit)

    fake_create = mocker.patch.object(datadog.api.Event, 'create')
    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version)

    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    dd_hook = uut.Hook()
    dd_hook.create_event(event)

    fake_create.assert_called_with(
        title='crane.deployment',
        text=text,
        tags=tags,
        alert_type=event,
    )
