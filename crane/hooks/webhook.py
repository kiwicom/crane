from datetime import datetime
from os import environ

import requests

from .base import Base


class Hook(Base):
    def __init__(self, deployment):
        super().__init__(deployment)
        self.urls = self.ctx.params["webhook_url"]
        self.token = self.ctx.params.get("webhook_token")

    def success(self):
        for url in self.urls:
            requests.post(
                url,
                headers={"Auth-Token": self.token},
                json={
                    "status": "success",
                    "version": self.deployment.new_version,
                    "ci_project_url": environ["CI_PROJECT_URL"],
                    "ci_job_id": environ["CI_JOB_ID"],
                    "gitlab_user_email": environ["GITLAB_USER_EMAIL"],
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
                    ],
                },
            )

    @property
    def is_active(self):
        return bool(self.ctx.params.get("webhook_url"))
