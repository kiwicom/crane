import re
import time
from os import environ
from time import time

import attr
import click
import git
import gitdb

from . import exc


@attr.s(slots=True)
class Base:

    ctx = attr.ib()
    repo = attr.ib(default=None)
    old_version = attr.ib(default=None)
    new_version = attr.ib(default=None)
    is_limited = attr.ib(default=False)

    @classmethod
    def from_context(cls, ctx):
        new_version = (
            ctx.params["new_image"].split(":")[-1]
            if ctx.params.get("new_image")
            else ctx.params.get("new_commit")
        )
        return cls(
            ctx=ctx, old_version=ctx.params.get("old_commit"), new_version=new_version
        )

    def check_preconditions(self):
        try:
            self.repo = git.Repo(environ["CI_PROJECT_DIR"])
        except (git.NoSuchPathError, KeyError):
            click.secho(
                f"You are not running crane in GitLab CI with a repository. "
                "crane is running in limited mode, all hooks have been disabled.",
                err=True,
                fg="red",
            )
            self.is_limited = True
            return
        try:
            self.new_commit
        except (gitdb.exc.BadName, ValueError):
            click.secho(
                f"The new version you specified, {self.new_version}, is not a valid git reference! "
                "crane is running in limited mode, all hooks have been disabled. "
                "It is highly recommended you use Git references for your deployments.",
                err=True,
                fg="red",
            )
            self.is_limited = True
            return

    @staticmethod
    def get_sha_from_image(old_image):
        version_matches = re.findall(r"\b[0-9a-f]{40}\b", old_image)
        if not version_matches:
            click.secho(
                "Your existing image seems to have no commit hash in its tag "
                + "for me to be able to upgrade to the new commit, "
                + f"but it's currently tagged as just :{old_image.split(':')[-1]} "
                + click.style("(๑′°︿°๑)", bold=True),
                err=True,
                fg="red",
            )
            raise exc.UpgradeFailed()
        elif len(version_matches) > 1:
            click.secho(
                "Your existing image seems to have multiple commit hashes in its tag, "
                + f"I don't know which one to replace, {', or'.join(version_matches)}! "
                + click.style("(｡•́︿•̀｡)", bold=True),
                err=True,
                fg="red",
            )
            raise exc.UpgradeFailed()
        return version_matches[0]

    @property
    def id(self):
        return f"{self.old_version}-{self.new_version}@{time()}"

    @property
    def commits(self):
        if self.is_disconnected:
            return [self.new_commit]
        elif self.is_redeploy:
            return []
        elif self.is_rollback:
            return list(
                self.repo.iter_commits(self.old_version + "..." + self.new_version)
            )
        return reversed(
            list(self.repo.iter_commits(self.old_version + "..." + self.new_version))
        )

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

    def upgrade(self):
        click.echo("Alrighty, let's deploy! " + click.style("ᕕ( ᐛ )ᕗ", bold=True))

        self.start_upgrade()
        self.wait_for_upgrade()

        if self.ctx.params["sleep_after_upgrade"]:
            click.echo(
                f'Upgrade done, waiting {self.ctx.params["sleep_after_upgrade"]}s as requested '
                + click.style("(ʃƪ˘･ᴗ･˘)", bold=True)
            )
            time.sleep(self.ctx.params["sleep_after_upgrade"])

        self.finish_upgrade()

    def start_upgrade(self):
        pass

    def wait_for_upgrade(self):
        pass

    def finish_upgrade(self):
        pass
