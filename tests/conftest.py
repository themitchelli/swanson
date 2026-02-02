"""
Pytest configuration for test suite.
"""

import sys
from pathlib import Path
import pytest

# Add project root to Python path to allow imports from setup.py and other modules
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def clear_executor_cache():
    """
    Clear the executor module cache before each test.

    This ensures tests don't interfere with each other due to cached values.
    """
    # Import here to avoid issues if module doesn't exist yet
    try:
        import executor
        # Clear the cache
        executor._cached_claude_path = None
    except (ImportError, AttributeError):
        # Module doesn't exist or cache doesn't exist yet - that's fine
        pass

    # Run the test
    yield

    # Clear cache after test as well
    try:
        import executor
        executor._cached_claude_path = None
    except (ImportError, AttributeError):
        pass
