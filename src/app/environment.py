"""
Module dedicated to interacting with the environment (variables, version.json)
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import AnyUrl, BaseSettings


class SentryDsn(AnyUrl):
    """Url type to validate Sentry DSN"""


class Settings(BaseSettings):
    """The Settings object extracts environment variables for convenience."""

    host: str = "0.0.0.0"
    port: str = "80"
    app_reload: bool = True
    env: str = "nonprod"

    # Jira
    jira_base_url: str = "https://mozit-test.atlassian.net/"
    jira_username: str
    jira_api_key: str

    # Bugzilla
    bugzilla_base_url: str = "https://bugzilla-dev.allizom.org"
    bugzilla_api_key: str

    # Logging
    log_level: str = "info"

    # Sentry
    sentry_dsn: Optional[SentryDsn]


@lru_cache()
def get_settings() -> Settings:
    """Return the Settings object; use cache"""
    return Settings()


@lru_cache()
def get_version():
    """Return contents of version.json. This has generic data in repo, but gets the build details in CI."""
    info = {}
    version_path = Path(__file__).parents[2] / "version.json"
    if version_path.exists():
        info = json.loads(version_path.read_text(encoding="utf8"))
    return info
