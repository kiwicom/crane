from os import environ
import re

import attr
import click
import git

from .exc import UpgradeFailed


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

        version_matches = re.findall(r'\b[0-9a-f]{40}\b', self.services[0].json()['launchConfig']['imageUuid'])
        if len(version_matches) != 1:
            click.secho('Your existing image tag must contain a commit SHA.', err=True, fg='red')
            raise UpgradeFailed()
        self.old_version = version_matches[0]
        self.new_version = settings['new_commit']
        self.check_preconditions()

    @property
    def id(self):
        return self.old_version + self.new_version

    @property
    def commits(self):
        if self.is_disconnected:
            return [self.new_commit]
        elif self.is_redeploy:
            return []
        elif self.is_rollback:
            return list(self.repo.iter_commits(self.old_version + '...' + self.new_version))
        return reversed(list(self.repo.iter_commits(self.old_version + '...' + self.new_version)))

    @property
    def old_commit(self):
        return self.repo.commit(self.old_version)

    @property
    def new_commit(self):
        return self.repo.commit(self.new_version)

    @property
    def is_rollback(self):
        return self.new_commit.committed_date < self.old_commit.committed_date

    @property
    def is_redeploy(self):
        return self.old_version == self.new_version

    @property
    def is_disconnected(self):
        """True if no path can be found from old commit to new commit."""
        try:
            return not (
                self.repo.is_ancestor(self.old_version, self.new_version)
                or self.repo.is_ancestor(self.new_version, self.old_version)
            )
        except git.GitCommandError:  # old commit was probably removed by force push or other black magic
            return True

    def check_preconditions(self):
        for service in self.services:
            if self.old_version not in service.json()['launchConfig']['imageUuid']:
                click.secho(
                    'All selected services must have the same commit SHA. '
                    'Please manually change their versions so they are all the same, and then retry the upgrade.',
                    err=True,
                    fg='red',
                )
                raise UpgradeFailed()
