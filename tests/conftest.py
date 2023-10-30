"""Bootstrap Pytest."""
import os


token_openai = os.getenv("OPENAI_TOKEN")


def pytest_configure(config):  # pylint: disable=unused-argument
    """Clean environment for tests."""
    if token_openai:
        del os.environ["OPENAI_TOKEN"]


def pytest_sessionfinish(session, exitstatus):  # pylint: disable=unused-argument
    """Recove environment after tests."""
    if token_openai:
        os.environ["OPENAI_TOKEN"] = token_openai
