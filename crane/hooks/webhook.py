from datetime import datetime
from os import environ
import requests

from .base import Base
from .. import deployment, settings


class Hook(Base):

    def __init__(self):
        self.urls = settings['webhook_url']

    def after_upgrade_success(self):
        for url in self.urls:
            requests.post(url, json={
                'status': 'success',
                'version': deployment.new_version,
                'ci_project_url': environ['CI_PROJECT_URL'],
                'ci_job_id': environ['CI_JOB_ID'],
                'gitlab_user_email': environ['GITLAB_USER_EMAIL'],
                'commits': [
                    {
                        'id': commit.hexsha,
                        'message': commit.message,
                        'author_name': commit.author.name,
                        'author_email': commit.author.email,
                        'timestamp': str(datetime.fromtimestamp(commit.committed_date + commit.committer_tz_offset)),
                    } for commit in deployment.commits
                ],
            })

    @property
    def is_active(self):
        return bool(settings.get('webhook_url'))
