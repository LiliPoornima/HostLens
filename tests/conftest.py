"""
conftest.py — pytest configuration for HostLens test suite.

Sets the working directory to the project root so that all tests can use
relative paths (e.g., 'data/processed/enriched_listings.csv') regardless of
where pytest is invoked from.
"""

import os
import pytest


def pytest_configure(config):
    """Change working directory to the project root before running tests."""
    # conftest.py lives in tests/, so project root is one level up
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(project_root)
