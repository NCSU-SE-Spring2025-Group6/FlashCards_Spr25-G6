# backend/test/conftest.py
import pytest
import sys
from pathlib import Path

@pytest.fixture(autouse=True)
def add_path():
    sys.path.append(str(Path(__file__).parent.parent))