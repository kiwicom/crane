from os import environ
import re

import attr
import click
import git
import gitdb.exc

from .exc import UpgradeFailed

@attr.s(slots=True)
class Deployment:

    stack = attr.ib(default=None)
    services = attr.ib(default=None)
    repo = attr.ib(default=None)
    old_version = attr.ib(default=None)
    new_version = attr.ib(default=None)
    is_limited = attr.ib(default=False)

    def load_from_settings(self, settings):
        from . import rancher  # here to prevent circular importing

        self.stack = rancher.Stack.from_name(settings['stack'])
        self.services = [self.stack.service_from_name(service) for service in settings['service']]

        old_image = self.services[0].json()['launchConfig']['imageUuid']

        if settings['new_image']:
            self.old_version = old_image.split(':')[-1]
            self.new_version = settings['new_image'].split(':')[-1]
        else:
            version_matches = re.findall(r'\b[0-9a-f]{40}\b', old_image)

            if not version_matches:
                click.secho(
                    'Your existing image seems to have no commit hash in its tag '
                    + 'for me to be able to upgrade to the new commit, '
                    + f"but it's currently tagged as just :{old_image.split(':')[-1]} "
                    + click.style('(๑′°︿°๑)', bold=True),
                    err=True,
                    fg='red',
                )
                raise UpgradeFailed()
            elif len(version_matches) > 1:
                click.secho(
                    'Your existing image seems to have multiple commit hashes in its tag, '
                    + f"I don't know which one to replace, {', or'.join(version_matches)}! "
                    + click.style('(｡•́︿•̀｡)', bold=True),
                    err=True,
                    fg='red',
                )
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
        from . import settings  # avoiding circular imports
        try:
            self.repo = git.Repo(environ['CI_PROJECT_DIR'])
        except git.NoSuchPathError:
            click.secho(
                f'You are not running crane in a Git repository. '
                'crane is running in limited mode, all hooks have been disabled. '
                'It is highly recommended you use Git references for your deployments.',
                err=True,
                fg='red',
            )
            self.is_limited = True
            return
        try:
            self.new_commit
        except gitdb.exc.BadName:
            click.secho(
                f'The new version you specified, {self.new_version}, is not a valid git reference! '
                'crane is running in limited mode, all hooks have been disabled. '
                'It is highly recommended you use Git references for your deployments.',
                err=True,
                fg='red',
            )
            self.is_limited = True
            return

        for service in self.services:
            if self.old_version not in service.json()['launchConfig']['imageUuid'] and not settings['new_image']:
                click.secho(
                    'All selected services must have the same commit SHA. '
                    'Please manually change their versions so they are all the same, and then retry the upgrade.',
                    err=True,
                    fg='red',
                )
                raise UpgradeFailed()
