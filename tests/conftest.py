"""Bootstrap Pytest."""

import os

token_openai = os.getenv("PARSER_OPENAI_API_KEY")


def pytest_configure(config):  # pylint: disable=unused-argument
    """Clean environment for tests."""
    if token_openai:
        del os.environ["PARSER_OPENAI_API_KEY"]


def pytest_sessionfinish(session, exitstatus):  # pylint: disable=unused-argument
    """Recove environment after tests."""
    if token_openai:
        os.environ["PARSER_OPENAI_API_KEY"] = token_openai
