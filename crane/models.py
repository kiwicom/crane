from os import environ

import attr
import git


@attr.s(slots=True)
class Deployment:

    stack = attr.ib(default=None)
    services = attr.ib(default=None)
    repo = attr.ib(default=None)
    old_version = attr.ib(default=None)
    new_version = attr.ib(default=None)

    def load_from_settings(self, settings):
        from . import rancher  # here to prevent circular importing

        self.stack = rancher.Stack.from_name(settings['stack'])
        self.services = [self.stack.service_from_name(service) for service in settings['service']]

        self.repo = git.Repo(environ['CI_PROJECT_DIR'])
        self.old_version = self.services[0].json()['launchConfig']['imageUuid'].split(':')[-1]
        self.new_version = settings.get('new_image',":").split(':')[-1]

    @property
    def id(self):
        return self.old_version + self.new_version

    @property
    def reverse_id(self):
        return self.new_version + self.old_version

    @property
    def commits(self):
        return list(self.repo.iter_commits(self.old_version + '...' + self.new_version))

    @property
    def is_redeploy(self):
        return self.old_version == self.new_version

    @property
    def old_commit(self):
        return self.repo.commit(self.old_version)

    @property
    def new_commit(self):
        return self.repo.commit(self.new_version)

    @property
    def is_rollback(self):
        return self.new_commit.committed_date < self.old_commit.committed_date
