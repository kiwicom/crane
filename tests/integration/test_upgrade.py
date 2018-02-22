import time

import pybreaker
import pytest
import requests

from crane import upgrade as uut, settings


class FakeService:
    log_name = "service_log_name"

    def __init__(self, state=None):
        self.state = state

    def start_upgrade(self):
        pass

    def finish_upgrade(self):
        pass

    def json(self):
        return {
            'state': self.state,
        }


def get_fake_check_state(exception_to_raise=None):

    def fake_check_state(services, done):
        if services:
            tmp = services - done
            done.add(tmp.pop())
        if exception_to_raise:
            raise exception_to_raise

    return fake_check_state


@pytest.mark.parametrize('count', [0, 1, 10])
def test_service_start_upgrade(mocker, count):
    fake_start_upgrade = mocker.patch.object(FakeService, 'start_upgrade')
    uut.service_start_upgrade([FakeService() for _ in range(count)])
    assert fake_start_upgrade.call_count == count


@pytest.mark.parametrize('count', [0, 1, 10])
def test_service_finish_upgrade(mocker, count):
    fake_finish_upgrade = mocker.patch.object(FakeService, 'finish_upgrade')
    uut.service_finish_upgrade([FakeService() for _ in range(count)])
    assert fake_finish_upgrade.call_count == count


@pytest.mark.parametrize(['states', 'raises'], [
    [[], False],
    [['upgrading'], False],
    [['upgraded'], False],
    [['foo'], True],
    [['upgraded', 'upgraded'], False],
    [['upgraded', 'upgraded', 'foo'], True],

])
def test_check_state(states, raises):
    services = [FakeService(state) for state in states]
    done = set()

    if raises:
        with pytest.raises(uut.UpgradeFailed):
            uut.check_state(services, done)
    else:
        uut.check_state(services, done)



@pytest.mark.parametrize(['services', 'sleep_count'], [
    [set(), 0],
    [set(range(1)), 1],
    [set(range(666)), 666],
])
def test_wait_for_upgrade_ok(mocker, services, sleep_count):
    uut.check_state = get_fake_check_state(None)
    fake_sleep = mocker.patch.object(time, 'sleep')
    uut.wait_for_upgrade(services)
    assert fake_sleep.call_count == sleep_count


@pytest.mark.parametrize(['services', 'error_raise', 'error_raised'], [
    [set(), pybreaker.CircuitBreakerError, None],
    [set(range(1)), pybreaker.CircuitBreakerError, uut.UpgradeFailed],
    [set(range(1)), requests.RequestException, None],
])
def test_wait_for_upgrade_error(services, error_raise, error_raised):
    uut.check_state = get_fake_check_state(error_raise)
    error = None
    try:
        uut.wait_for_upgrade(services)
    except Exception as e:
        error = e

    if error_raised:
        assert isinstance(error, error_raised)
    else:
        assert not error


@pytest.mark.parametrize(['sleep_after_upgrade', 'manual_finish'], [
    [0, True],
    [1, True],
    [1, False],
])
def test_after_upgrade(monkeypatch, mocker, sleep_after_upgrade, manual_finish):
    services = set(range(42))
    monkeypatch.setitem(settings, 'sleep_after_upgrade', sleep_after_upgrade)
    monkeypatch.setitem(settings, 'manual_finish', manual_finish)

    fake_sleep = mocker.patch.object(time, 'sleep')
    fake_service_finish_upgrade = mocker.patch.object(uut, 'service_finish_upgrade')

    uut.after_upgrade(services)

    if sleep_after_upgrade:
        fake_sleep.assert_called_with(sleep_after_upgrade)
    else:
        assert fake_sleep.call_count == 0

    if not manual_finish:
        fake_service_finish_upgrade.assert_called_with(services)
    else:
        assert fake_service_finish_upgrade.call_count == 0
