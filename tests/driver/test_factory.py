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
from unittest.mock import MagicMock, patch

import pytest

from graphiti_core.driver.driver import GraphDriver
from graphiti_core.driver.factory import DriverFactory


class TestDriverFactory:
    """Test the DriverFactory class."""

    @patch.dict(os.environ, {}, clear=True)
    @patch('graphiti_core.driver.factory.Neo4jDriver')
    def test_create_driver_defaults_to_neo4j(self, mock_neo4j_driver_class):
        """Test that factory defaults to Neo4j when no GRAPHITI_DB_TYPE is set."""
        mock_driver = MagicMock(spec=GraphDriver)
        mock_neo4j_driver_class.return_value = mock_driver

        driver = DriverFactory.create_driver('bolt://localhost:7687', 'neo4j', 'password')

        mock_neo4j_driver_class.assert_called_once_with(
            'bolt://localhost:7687', 'neo4j', 'password'
        )
        assert driver is mock_driver

    @patch.dict(os.environ, {'GRAPHITI_DB_TYPE': 'neo4j'})
    @patch('graphiti_core.driver.factory.Neo4jDriver')
    def test_create_driver_explicit_neo4j(self, mock_neo4j_driver_class):
        """Test that factory creates Neo4j driver when explicitly configured."""
        mock_driver = MagicMock(spec=GraphDriver)
        mock_neo4j_driver_class.return_value = mock_driver

        driver = DriverFactory.create_driver('bolt://localhost:7687', 'neo4j', 'password')

        mock_neo4j_driver_class.assert_called_once_with(
            'bolt://localhost:7687', 'neo4j', 'password'
        )
        assert driver is mock_driver

    @patch.dict(os.environ, {'GRAPHITI_DB_TYPE': 'falkordb'})
    def test_create_driver_falkordb(self):
        """Test that factory creates FalkorDB driver when configured."""
        with patch('graphiti_core.driver.falkordb_driver.FalkorDriver') as mock_falkor_driver_class:
            mock_driver = MagicMock(spec=GraphDriver)
            mock_falkor_driver_class.return_value = mock_driver

            driver = DriverFactory.create_driver()

            mock_falkor_driver_class.assert_called_once_with()
            assert driver is mock_driver

    @patch.dict(os.environ, {'GRAPHITI_DB_TYPE': 'neo4j'})
    def test_create_driver_neo4j_requires_uri(self):
        """Test that factory raises ValueError when Neo4j is selected without URI."""
        with pytest.raises(ValueError, match='uri must be provided when using Neo4j driver'):
            DriverFactory.create_driver(uri=None)

    @patch.dict(os.environ, {'GRAPHITI_DB_TYPE': 'falkordb'})
    def test_create_driver_falkordb_import_error(self):
        """Test that factory raises helpful error when FalkorDB is not installed."""
        with patch(
            'graphiti_core.driver.falkordb_driver.FalkorDriver',
            side_effect=ImportError("No module named 'falkordb'"),
        ), pytest.raises(ImportError, match='FalkorDB driver is not available'):
            DriverFactory.create_driver()

    @patch.dict(os.environ, {'GRAPHITI_DB_TYPE': 'invalid'})
    def test_create_driver_unsupported_database_type(self):
        """Test that factory raises ValueError for unsupported database types."""
        with pytest.raises(ValueError, match='Unsupported database type: invalid'):
            DriverFactory.create_driver()

    @patch.dict(os.environ, {'GRAPHITI_DB_TYPE': 'FALKORDB'})
    def test_create_driver_case_insensitive(self):
        """Test that factory handles case insensitive database type values."""
        with patch('graphiti_core.driver.falkordb_driver.FalkorDriver') as mock_falkor_driver_class:
            mock_driver = MagicMock(spec=GraphDriver)
            mock_falkor_driver_class.return_value = mock_driver

            driver = DriverFactory.create_driver()

            mock_falkor_driver_class.assert_called_once_with()
            assert driver is mock_driver

    @patch.dict(os.environ, {'GRAPHITI_DB_TYPE': 'neo4j'})
    @patch('graphiti_core.driver.factory.Neo4jDriver')
    def test_create_driver_with_config_parameter(self, mock_neo4j_driver_class):
        """Test that factory accepts config parameter (currently unused but reserved)."""
        mock_driver = MagicMock(spec=GraphDriver)
        mock_neo4j_driver_class.return_value = mock_driver

        config = {'some': 'config'}
        driver = DriverFactory.create_driver('bolt://localhost:7687', 'neo4j', 'password', config)

        # Config should be accepted but not used
        mock_neo4j_driver_class.assert_called_once_with(
            'bolt://localhost:7687', 'neo4j', 'password'
        )
        assert driver is mock_driver
