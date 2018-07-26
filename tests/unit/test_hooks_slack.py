import pytest

from crane import settings
from crane.exc import UpgradeFailed
from crane.hooks.slack import Hook as SlackHook


def test_without_slack_channel(monkeypatch):
    monkeypatch.setitem(settings, 'slack_token', 'some token')
    monkeypatch.setitem(settings, 'slack_channel', None)

    with pytest.raises(UpgradeFailed):
        SlackHook()


def test_without_slack_token(monkeypatch):
    monkeypatch.setitem(settings, 'slack_token', None)
    monkeypatch.setitem(settings, 'slack_channel', 'some channel')

    with pytest.raises(UpgradeFailed):
        SlackHook()
