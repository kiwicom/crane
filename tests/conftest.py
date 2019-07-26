from collections import defaultdict
from datetime import datetime

import git
import pytest
import tempfile

from git import Actor


@pytest.fixture(autouse=True)
def gitlab_ci_env(monkeypatch):
    monkeypatch.setenv("GITLAB_USER_EMAIL", "picky@kiwi.com")
    monkeypatch.setenv("CI_PROJECT_PATH", "foo/bar")
    monkeypatch.setenv("CI_PROJECT_URL", "https://example.com/foo/bar")
    monkeypatch.setenv("CI_JOB_ID", "1234567")
    monkeypatch.setenv("CI_REGISTRY_IMAGE", "registry.example.com/foo/bar")
    monkeypatch.setenv("CI_ENVIRONMENT_NAME", "a-b/c-d")


@pytest.fixture
def repo():
    ts = datetime(2018, 1, 1, 0, 0, 0).isoformat()
    with tempfile.TemporaryDirectory() as repo_dir:
        repo = git.Repo.init(repo_dir)
        repo.index.commit(
            "Initial commit",
            author=Actor("test_author", "test@test.com"),
            commit_date=ts,
        )
        yield repo
