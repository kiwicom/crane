import os
import shutil

import git
import pytest
import tempfile
from crane import deployment


@pytest.fixture(autouse=True)
def gitlab_ci_env(monkeypatch):
    monkeypatch.setenv("GITLAB_USER_EMAIL", "picky@kiwi.com")
    monkeypatch.setenv("CI_PROJECT_PATH", "foo/bar")
    monkeypatch.setenv("CI_PROJECT_URL", "https://example.com/foo/bar")
    monkeypatch.setenv("CI_JOB_ID", "1234567")
    monkeypatch.setenv("CI_REGISTRY_IMAGE", "registry.example.com/foo/bar")
    monkeypatch.setenv("CI_ENVIRONMENT_NAME", "a-b/c-d")
