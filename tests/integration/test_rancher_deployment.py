import time

import pybreaker
import pytest
import requests

import crane
import crane.exc
from crane.rancher import deployment as uut


@pytest.fixture
def fake_deployment(repo):
    return uut.Deployment(repo=repo, old_version="HEAD", new_version="HEAD")


class FakeService:
    log_name = "service_log_name"

    def __init__(self, state=None):
        self.state = state

    def start_upgrade(self):
        pass

    def finish_upgrade(self):
        pass

    def json(self):
        return {"state": self.state}


@pytest.mark.parametrize(
    ["states", "raises"],
    [
        [[], False],
        [["upgrading"], False],
        [["upgraded"], False],
        [["foo"], True],
        [["upgraded", "upgraded"], False],
        [["upgraded", "upgraded", "foo"], True],
    ],
)
def test_check_state(fake_deployment, states, raises):
    services = [FakeService(state) for state in states]
    fake_deployment.services = services
    already_upgraded = set()

    if raises:
        with pytest.raises(crane.exc.UpgradeFailed):
            list(fake_deployment.get_upgraded_services(already_upgraded))
    else:
        list(fake_deployment.get_upgraded_services(already_upgraded))


@pytest.mark.parametrize(
    ["services", "sleep_count"], [[set(), 0], [range(1), 1], [range(666), 666]]
)
def test_wait_for_upgrade_ok(fake_deployment, mocker, services, sleep_count):
    def upgrade_services_one_by_one(all_services):
        all_services = list(all_services)
        already_upgraded = []
        while True:
            already_upgraded.append(all_services.pop())
            yield already_upgraded

    fake_deployment.services = services

    mocker.patch.object(
        fake_deployment,
        "get_upgraded_services",
        side_effect=upgrade_services_one_by_one(services),
    )
    fake_sleep = mocker.patch.object(time, "sleep")

    fake_deployment.wait_for_upgrade()
    assert fake_sleep.call_count == sleep_count


@pytest.mark.parametrize(
    ["services", "side_effect", "expected_error"],
    [
        [set(), pybreaker.CircuitBreakerError, None],
        [
            set(range(1)),
            [requests.RequestException, pybreaker.CircuitBreakerError],
            crane.exc.UpgradeFailed,
        ],
        [set(range(1)), 10 * [requests.RequestException] + [None], None],
    ],
)
def test_wait_for_upgrade_error(
    fake_deployment, mocker, services, side_effect, expected_error
):
    fake_deployment.services = services
    mocker.patch.object(time, "sleep")
    mocker.patch.object(
        fake_deployment, "get_upgraded_services", side_effect=side_effect
    )

    with pytest.raises(Exception) as e:
        fake_deployment.wait_for_upgrade()
        if expected_error:
            assert isinstance(e, expected_error)
        else:
            assert not e
