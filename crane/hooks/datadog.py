from functools import partial
from os import environ

import datadog

from .. import deployment, settings
from .base import Base


class Hook(Base):

    def __init__(self):
        datadog.initialize(api_key=settings['datadog_api_key'])

    def create_event(self, alert_type):
        datadog.api.Event.create(
            title='{0} deployment'.format(environ["CI_PROJECT_PATH"]),
            text='\n'.join(commit.summary for commit in reversed(deployment.commits)),
            tags=['releaser:{0}'.format(environ['GITLAB_USER_EMAIL']),
                  'project:{0}'.format(environ['CI_PROJECT_PATH'])],
            alert_type=alert_type,
        )

    after_upgrade_success = partial(create_event, 'success')
    after_upgrade_failure = partial(create_event, 'error')

    @property
    def is_active(self):
        return bool(settings.get('datadog_api_key'))
