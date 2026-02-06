import pytest

def test_fail_only_for_debugging() -> None:
    """This test is designed to fail and should be used only for debugging purposes."""
    assert False, "This test is intentionally failing for debugging purposes."