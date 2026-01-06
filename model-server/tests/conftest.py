import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(autouse=True)
def mock_rag_engine():
    with patch("app.agent.handlers.rag_engine") as mock_rag:
        mock_rag.search.return_value = [
            "Classic Burger - $8.99",
            "Cheese Burger - $9.99",
            "Bacon Burger - $10.99",
        ]
        yield mock_rag


@pytest.fixture(autouse=True)
def mock_environment_variables(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-api-key")
    monkeypatch.setenv("PINECONE_INDEX_NAME", "test-index")
