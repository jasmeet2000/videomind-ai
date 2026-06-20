"""
Pytest shared fixtures and configuration.
Applied to all tests in the test suite.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Ensure the lru_cache on get_settings() is cleared between tests
# so that env-variable-patching tests don't leak state.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clear the get_settings() lru_cache before and after every test.

    Without this, patching os.environ in one test leaks into the next
    because lru_cache returns the cached Settings instance regardless
    of env changes.
    """
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
