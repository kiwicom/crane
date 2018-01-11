import pytest
import tempfile
import git
import requests

from crane.hooks import slack as uut
from crane import settings, Deployment,rancher


@pytest.fixture(autouse=True)
def click_setting(monkeypatch):
    monkeypatch.setitem(settings, 'slack_token', '')
    monkeypatch.setitem(settings, 'slack_channel', '')
    monkeypatch.setitem(settings, 'slack_link', '')
    monkeypatch.setitem(settings, 'url', 'asd')
    monkeypatch.setitem(settings, 'env', 'asd')
    monkeypatch.setitem(settings, 'stack', 'asd')

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
    assert slack_hook.get_changelog() == result



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

    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version, stack=rancher.Stack('0st0', 'foo'))
    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    slack_hook = uut.Hook()
    slack_hook.users_by_email = {'picky@kiwi.com': "@picky"}

    assert slack_hook.generate_new_message().items() == result.items()



@pytest.mark.parametrize(['message', 'url', 'result_message', 'base_data'], [
    [{
        'attachments': [
            {
                'fields': {
                    'Environment': ':x:'
                }
            }
        ]
    }, '', {}, {}]
])
def test_send_message(monkeypatch, mocker, repo, message, url, result_message, base_data):
    old_version = repo.head.commit.hexsha
    repo.index.commit('1')

    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version)
    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    fake_post = mocker.patch.object(requests.Session, 'post')

    slack_hook = uut.Hook()
    slack_hook.channel_id = 'asd'

    slack_hook.send_message(message)

    fake_post.assert_called_with(url, data={**base_data, **result_message, 'link_names':'1'})

@pytest.mark.parametrize(['commits', 'event', 'text', 'tags'], [
    [['1'], 'success', '1', ['author:picky@kiwi.com', 'project:foo-bar']],
])
def test_send_reply(monkeypatch, mocker, repo, commits, event, text, tags):
    old_version = repo.head.commit.hexsha
    for commit in commits:
        repo.index.commit(commit)

    fake_post = mocker.patch.object(requests.Session, 'post')
    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version)

    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    slack_hook = uut.Hook()
    slack_hook.channel_id = 'asd'
    slack_hook.send_reply(event, text)

    fake_post.assert_called_with(
        title='crane.deployment',
        text=text,
        tags=tags,
        alert_type=event,
    )

@pytest.mark.parametrize(['event', 'text', 'tags'],
    []
)
def test_set_status(monkeypatch, mocker, ):
    old_version = repo.head.commit.hexsha
    for commit in ['1']:
        repo.index.commit(commit)

    fake_post = mocker.patch.object(requests.Session, 'post')
    fake_deployment = Deployment(repo=repo, new_version='HEAD', old_version=old_version)

    monkeypatch.setattr(uut, 'deployment', fake_deployment)

    slack_hook = uut.Hook()
    slack_hook.channel_id = 'asd'
    slack_hook.send_reply(event, text)

    fake_post.assert_called_with(
        title='crane.deployment',
        text=text,
        tags=tags,
        alert_type=event,
    )

def test_before_upgrade():
    pass


def test_after_upgrade_success():
    pass


def test_after_upgrade_failure():
    pass
