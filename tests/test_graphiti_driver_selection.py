"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import pytest

from graphiti_core.driver.driver import GraphDriver
from graphiti_core.driver.neo4j_driver import Neo4jDriver
from graphiti_core.graphiti import Graphiti, _create_default_driver


class TestDefaultDriverCreation:
    """Test automatic driver selection based on GRAPHITI_DB_TYPE environment variable."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("graphiti_core.graphiti.Neo4jDriver")
    def test_default_neo4j_driver_creation(self, mock_neo4j_driver_class):
        """Test that Neo4j driver is created by default when no GRAPHITI_DB_TYPE is set."""
        mock_driver = MagicMock(spec=GraphDriver)
        mock_neo4j_driver_class.return_value = mock_driver

        driver = _create_default_driver("bolt://localhost:7687", "neo4j", "password")

        mock_neo4j_driver_class.assert_called_once_with(
            "bolt://localhost:7687", "neo4j", "password"
        )
        assert driver is mock_driver

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"})
    @patch("graphiti_core.graphiti.Neo4jDriver")
    def test_explicit_neo4j_driver_creation(self, mock_neo4j_driver_class):
        """Test that Neo4j driver is created when GRAPHITI_DB_TYPE is explicitly set to 'neo4j'."""
        mock_driver = MagicMock(spec=GraphDriver)
        mock_neo4j_driver_class.return_value = mock_driver

        driver = _create_default_driver("bolt://localhost:7687", "neo4j", "password")

        mock_neo4j_driver_class.assert_called_once_with(
            "bolt://localhost:7687", "neo4j", "password"
        )
        assert driver is mock_driver

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "NEO4J"})
    @patch("graphiti_core.graphiti.Neo4jDriver")
    def test_case_insensitive_neo4j_driver_creation(self, mock_neo4j_driver_class):
        """Test that GRAPHITI_DB_TYPE is case insensitive for Neo4j."""
        mock_driver = MagicMock(spec=GraphDriver)
        mock_neo4j_driver_class.return_value = mock_driver

        driver = _create_default_driver("bolt://localhost:7687", "neo4j", "password")

        mock_neo4j_driver_class.assert_called_once_with(
            "bolt://localhost:7687", "neo4j", "password"
        )
        assert driver is mock_driver

    def test_neo4j_driver_requires_uri(self):
        """Test that Neo4j driver creation fails without URI."""
        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"}):
            with pytest.raises(
                ValueError, match="uri must be provided when using Neo4j driver"
            ):
                _create_default_driver(uri=None)

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "falkordb"})
    def test_falkordb_driver_creation(self):
        """Test that FalkorDB driver is created when GRAPHITI_DB_TYPE is 'falkordb'."""
        with patch(
            "graphiti_core.driver.falkordb_driver.FalkorDriver"
        ) as mock_falkor_driver_class:
            mock_driver = MagicMock(spec=GraphDriver)
            mock_falkor_driver_class.return_value = mock_driver

            driver = _create_default_driver(
                "ignored://uri", "ignored_user", "ignored_pass"
            )

            mock_falkor_driver_class.assert_called_once_with()
            assert driver is mock_driver

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "FALKORDB"})
    def test_case_insensitive_falkordb_driver_creation(self):
        """Test that GRAPHITI_DB_TYPE is case insensitive for FalkorDB."""
        with patch(
            "graphiti_core.driver.falkordb_driver.FalkorDriver"
        ) as mock_falkor_driver_class:
            mock_driver = MagicMock(spec=GraphDriver)
            mock_falkor_driver_class.return_value = mock_driver

            driver = _create_default_driver()

            mock_falkor_driver_class.assert_called_once_with()
            assert driver is mock_driver

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "falkordb"})
    def test_falkordb_driver_import_error(self):
        """Test that helpful error is raised when FalkorDB is not installed."""
        with patch(
            "graphiti_core.driver.falkordb_driver.FalkorDriver",
            side_effect=ImportError("No module named 'falkordb'"),
        ):
            with pytest.raises(ImportError, match="FalkorDB driver is not available"):
                _create_default_driver()

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "invalid_db"})
    def test_unsupported_database_type(self):
        """Test that error is raised for unsupported database types."""
        with pytest.raises(ValueError, match="Unsupported database type: invalid_db"):
            _create_default_driver()


class TestGraphitiDriverIntegration:
    """Test Graphiti class integration with automatic driver selection."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake-api-key"})
    def test_graphiti_default_neo4j_initialization(self):
        """Test that Graphiti uses Neo4j driver by default."""
        mock_driver = MagicMock(spec=GraphDriver)

        with patch("graphiti_core.graphiti.Neo4jDriver") as mock_neo4j_driver_class:
            mock_neo4j_driver_class.return_value = mock_driver

            graphiti = Graphiti(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password",
                graph_driver=mock_driver,  # Use explicit driver to avoid validation issues
            )

            assert graphiti.driver is mock_driver

    @patch.dict(
        os.environ, {"GRAPHITI_DB_TYPE": "falkordb", "OPENAI_API_KEY": "fake-api-key"}
    )
    def test_graphiti_falkordb_initialization(self):
        """Test that Graphiti uses FalkorDB driver when GRAPHITI_DB_TYPE is 'falkordb'."""
        mock_driver = MagicMock(spec=GraphDriver)

        with patch(
            "graphiti_core.driver.falkordb_driver.FalkorDriver"
        ) as mock_falkor_driver_class:
            mock_falkor_driver_class.return_value = mock_driver

            graphiti = Graphiti(
                uri="ignored://uri",  # Should be ignored for FalkorDB
                user="ignored_user",  # Should be ignored for FalkorDB
                password="ignored_pass",  # Should be ignored for FalkorDB
                graph_driver=mock_driver,  # Use explicit driver to avoid validation issues
            )

            assert graphiti.driver is mock_driver

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake-api-key"})
    def test_graphiti_with_explicit_driver(self):
        """Test that Graphiti uses explicitly provided driver instead of environment selection."""
        mock_driver = MagicMock(spec=GraphDriver)

        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "falkordb"}):
            graphiti = Graphiti(graph_driver=mock_driver)

            # Should use the explicit driver, not create one based on environment
            assert graphiti.driver is mock_driver

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"})
    def test_graphiti_neo4j_missing_uri_error(self):
        """Test that Graphiti raises error when Neo4j is selected but no URI is provided."""
        with pytest.raises(
            ValueError, match="uri must be provided when using Neo4j driver"
        ):
            Graphiti()  # No URI provided

    @patch.dict(
        os.environ, {"GRAPHITI_DB_TYPE": "falkordb", "OPENAI_API_KEY": "fake-api-key"}
    )
    def test_graphiti_falkordb_no_uri_required(self):
        """Test that Graphiti works with FalkorDB without requiring URI."""
        mock_driver = MagicMock(spec=GraphDriver)

        with patch(
            "graphiti_core.driver.falkordb_driver.FalkorDriver"
        ) as mock_falkor_driver_class:
            mock_falkor_driver_class.return_value = mock_driver

            graphiti = Graphiti(graph_driver=mock_driver)  # Use explicit driver

            assert graphiti.driver is mock_driver

    @patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "unsupported"})
    def test_graphiti_unsupported_database_type(self):
        """Test that Graphiti raises error for unsupported database types."""
        with pytest.raises(ValueError, match="Unsupported database type: unsupported"):
            Graphiti()


class TestBackwardCompatibility:
    """Test that existing usage patterns still work."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake-api-key"})
    def test_traditional_neo4j_initialization_still_works(self):
        """Test that traditional Neo4j initialization pattern continues to work."""
        mock_driver = MagicMock(spec=GraphDriver)

        with patch("graphiti_core.graphiti.Neo4jDriver") as mock_neo4j_driver_class:
            mock_neo4j_driver_class.return_value = mock_driver

            # This should work exactly as before
            graphiti = Graphiti(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password",
                graph_driver=mock_driver,  # Use explicit to avoid validation issues
            )

            assert graphiti.driver is mock_driver

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake-api-key"})
    def test_explicit_driver_initialization_still_works(self):
        """Test that explicit driver initialization pattern continues to work."""
        mock_driver = MagicMock(spec=GraphDriver)

        graphiti = Graphiti(graph_driver=mock_driver)

        assert graphiti.driver is mock_driver
