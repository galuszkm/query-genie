import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Add project root to path so 'src' module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def clear_rate_limiter() -> Generator[None]:
    """Clear rate limiter state before each test to prevent cross-test pollution."""
    from src.utils.validators import _LAST_CALL

    _LAST_CALL.clear()
    yield
    _LAST_CALL.clear()
