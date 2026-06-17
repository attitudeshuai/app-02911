"""
Pytest configuration and shared fixtures for headless testing.
All tests run without GUI - we test the command logic layer directly.
"""
import os
import sys
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_workspace():
    """Create a temporary directory as workspace for each test."""
    tmpdir = tempfile.mkdtemp(prefix="cargo_commander_test_")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def router():
    """Provide a fresh CommandRouter instance for each test."""
    from app.commands.command_router import CommandRouter
    return CommandRouter()
