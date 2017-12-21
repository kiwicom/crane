import pytest
import datadog
from crane.hooks import datadog as uut
from crane import settings


@pytest.fixture(autouse=True)
def click_settings(monkeypatch):
    monkeypatch.setitem(settings, 'datadog_api_key', '')
    monkeypatch.setitem(settings, 'datadog_app_key', '')


def test_create_event(mocker):
    fake_create = mocker.patch.object(datadog.api.Event, 'create')

    fake_deployment = mocker.patch.object(uut, 'deployment')
    fake_deployment.commits = []

    dd_hook = uut.Hook()
    dd_hook.create_event('success')

    fake_create.assert_called_with(
        title='crane.deployment',
        text='',
        priority='normal',
        tags=['author:picky@kiwi.com', 'project:gitlab.skypicker.com/fooo/foo'],
        alert_type='success',
    )
