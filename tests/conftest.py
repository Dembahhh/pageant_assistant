"""Shared fixtures and markers for the Pageant Assistant test suite."""

import os

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires GROQ_API_KEY (may incur API costs)")


@pytest.fixture
def groq_key():
    """Return the Groq API key or skip the test if unavailable."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        pytest.skip("GROQ_API_KEY not set — skipping integration test")
    return key
