from datetime import datetime
from os import environ

import requests

from .base import Base

session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=5, pool_maxsize=5, max_retries=3
)
session.mount("http://", _adapter)
session.mount("https://", _adapter)


class Hook(Base):
    def __init__(self, deployment):
        super().__init__(deployment)
        self.webhook = self.ctx.params["sentry_webhook"]

    def success(self):
        session.post(
            f"{self.webhook}/",
            json={
                "version": self.deployment.new_version,
                "url": f'{environ["CI_PROJECT_URL"]}/builds/{environ["CI_JOB_ID"]}',
                "commits": [
                    {
                        "id": commit.hexsha,
                        "message": commit.message,
                        "author_name": commit.author.name,
                        "author_email": commit.author.email,
                        "timestamp": str(
                            datetime.fromtimestamp(
                                commit.committed_date + commit.committer_tz_offset
                            )
                        ),
                    }
                    for commit in self.deployment.commits
                    if not self.deployment.is_rollback
                ],
            },
        )

    @property
    def is_active(self):
        return bool(self.ctx.params.get("sentry_webhook"))
