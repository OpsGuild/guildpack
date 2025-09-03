import pytest
import sys
import os

# Add the python directory to the path so we can import oguild
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure pytest for async tests
pytest_plugins = ['pytest_asyncio']

