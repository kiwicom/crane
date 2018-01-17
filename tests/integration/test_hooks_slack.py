import pytest
import tempfile
import git
import requests

from crane.hooks import slack as uut
from crane import settings, Deployment



@pytest.fixture(autouse=True)
def click_setting(monkeypatch):
    monkeypatch.setitem(settings, 'slack_token', '')
    monkeypatch.setitem(settings, 'slack_channel', '')
    monkeypatch.setitem(settings, 'slack_link', '')

@pytest.fixture
def repo():
    with tempfile.TemporaryDirectory() as repo_dir:
        repo = git.Repo.init(repo_dir)
        repo.index.commit('Initial commit')
        yield repo



def test_get_existing_message():
    pass


@pytest.mark.parametrize(['commits', 'result'], [
    [['1', '2'], '']
])
def get_changelog(monkeypatch, repo, commits, result):
    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit)

    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version)
    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    slack_hook = uut.Hook()
    assert(slack_hook.get_changelog(), result)



@pytest.mark.parametrize(['commits','path', 'url', 'job_id', 'ci_environmner_url', 'result'], [
    [['1'], '', '', '', '', {}]
])
def test_generate_new_mesage(monkeypatch, repo, commits, path, url, job_id, ci_environmner_url, result):
    monkeypatch.setenv('CI_PROJECT_PATH', path)
    monkeypatch.setenv('CI_PROJECT_URL', url)
    monkeypatch.setenv('CI_JOB_ID', job_id)
    monkeypatch.setenv('CI_ENVIRONMENT_URL', ci_environmner_url)

    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit)

    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version)
    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    slack_hook = uut.Hook()


    assert(slack_hook.generate_new_message(), result)


@pytest.mark.parametrize(['message', 'url', 'result_message', 'base_data'], [
    [['1', '2'], '', {}, {}]
])
def test_send_message(monkeypatch, mocker, repo, message, url, result_message, base_data):
    old_version = repo.head.commit.hexsha
    for commit in ['1']:
        repo.index.commit(commit)
    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version)
    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    fake_post = mocker.patch.object(requests.Session, 'post')

    slack_hook = uut.Hook()
    slack_hook.send_message(message)

    fake_post.assert_called_with(url, data={**base_data, **result_message, 'link_names':'1'})


def test_send_reply():
    pass


def test_set_status():
    pass


def test_before_upgrade():
    pass


def test_after_upgrade_success():
    pass


def test_after_upgrade_failure():
    pass

@pytest.mark.parametrize(['commit', 'people'], [
    ['', []]
])
def test_get_tagged_people(commit, people):
    pass