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

try:
    from graphiti_core.driver.falkordb_driver import FalkorDBConfig, FalkorDriver

    HAS_FALKORDB = True
except ImportError:
    FalkorDBConfig = None
    FalkorDriver = None
    HAS_FALKORDB = False


class TestFalkorDBConfig:
    """Test FalkorDB configuration class."""

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_default_values(self):
        """Test FalkorDBConfig default values."""
        config = FalkorDBConfig()

        assert config.host == 'localhost'
        assert config.port == 6379
        assert config.database == 0
        assert config.password is None
        assert config.connection_string is None

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_custom_values(self):
        """Test FalkorDBConfig with custom values."""
        config = FalkorDBConfig(host='custom-host', port=9999, database=5, password='secret')

        assert config.host == 'custom-host'
        assert config.port == 9999
        assert config.database == 5
        assert config.password == 'secret'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_port_validation(self):
        """Test port validation."""
        # Valid port
        config = FalkorDBConfig(port=8080)
        assert config.port == 8080

        # Invalid ports
        with pytest.raises(ValueError, match='Port must be between 1 and 65535'):
            FalkorDBConfig(port=0)

        with pytest.raises(ValueError, match='Port must be between 1 and 65535'):
            FalkorDBConfig(port=65536)

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_database_validation(self):
        """Test database number validation."""
        # Valid database
        config = FalkorDBConfig(database=10)
        assert config.database == 10

        # Invalid database
        with pytest.raises(ValueError, match='Database number must be non-negative'):
            FalkorDBConfig(database=-1)

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_connection_string_validation(self):
        """Test connection string validation."""
        # Valid connection strings
        valid_strings = [
            'redis://localhost:6379/0',
            'redis://:password@localhost:6379/0',
            'redis://user:password@host:6379/1',
            'redis://host:6379',
            'redis://host',
        ]

        for conn_str in valid_strings:
            config = FalkorDBConfig(connection_string=conn_str)
            assert config.connection_string == conn_str

        # Invalid connection strings
        invalid_strings = [
            '',
            '   ',
            'http://localhost:6379/0',  # Wrong scheme
            'localhost:6379',  # No scheme
            'redis://',  # Empty
        ]

        for conn_str in invalid_strings:
            with pytest.raises(ValueError):
                FalkorDBConfig(connection_string=conn_str)

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_defaults(self):
        """Test from_env with no environment variables uses defaults."""
        config = FalkorDBConfig.from_env()

        assert config.host == 'localhost'
        assert config.port == 6379
        assert config.database == 0
        assert config.password is None

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch.dict(
        os.environ,
        {
            'FALKORDB_HOST': 'test-host',
            'FALKORDB_PORT': '7000',
            'FALKORDB_DATABASE': '3',
            'FALKORDB_PASSWORD': 'test-password',
        },
    )
    def test_from_env_individual_variables(self):
        """Test from_env with individual environment variables."""
        config = FalkorDBConfig.from_env()

        assert config.host == 'test-host'
        assert config.port == 7000
        assert config.database == 3
        assert config.password == 'test-password'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch.dict(os.environ, {'FALKORDB_CONNECTION_STRING': 'redis://:secret@remote-host:8000/5'})
    def test_from_env_connection_string_takes_precedence(self):
        """Test that connection string takes precedence over individual variables."""
        with patch.dict(
            os.environ,
            {
                'FALKORDB_HOST': 'ignored-host',
                'FALKORDB_PORT': '9999',
                'FALKORDB_DATABASE': '99',
                'FALKORDB_PASSWORD': 'ignored-password',
                'FALKORDB_CONNECTION_STRING': 'redis://:secret@remote-host:8000/5',
            },
        ):
            config = FalkorDBConfig.from_env()

            # Should use connection string values, not individual env vars
            assert config.host == 'remote-host'
            assert config.port == 8000
            assert config.database == 5
            assert config.password == 'secret'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_from_connection_string_basic(self):
        """Test basic connection string parsing."""
        config = FalkorDBConfig.from_connection_string('redis://localhost:6379/0')

        assert config.host == 'localhost'
        assert config.port == 6379
        assert config.database == 0
        assert config.password is None
        assert config.connection_string == 'redis://localhost:6379/0'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_from_connection_string_with_password(self):
        """Test connection string with password."""
        config = FalkorDBConfig.from_connection_string('redis://:mypassword@example.com:9999/3')

        assert config.host == 'example.com'
        assert config.port == 9999
        assert config.database == 3
        assert config.password == 'mypassword'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_from_connection_string_minimal(self):
        """Test minimal connection string."""
        config = FalkorDBConfig.from_connection_string('redis://host')

        assert config.host == 'host'
        assert config.port == 6379  # Default
        assert config.database == 0  # Default
        assert config.password is None

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_from_connection_string_defaults_hostname(self):
        """Test connection string defaults hostname when missing."""
        config = FalkorDBConfig.from_connection_string('redis://:password@:7000/2')

        assert config.host == 'localhost'  # Default when hostname empty
        assert config.port == 7000
        assert config.database == 2
        assert config.password == 'password'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_from_connection_string_invalid_format(self):
        """Test invalid connection string formats."""
        invalid_strings = [
            '',
            'http://localhost:6379/0',  # Wrong scheme
            'redis://',  # No host
            'redis://host:invalid/0',  # Invalid port
            'redis://host:6379/invalid',  # Invalid database
        ]

        for conn_str in invalid_strings:
            with pytest.raises(ValueError):
                FalkorDBConfig.from_connection_string(conn_str)

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_get_client_kwargs(self):
        """Test get_client_kwargs method."""
        config = FalkorDBConfig(host='test-host', port=8080, password='secret')

        kwargs = config.get_client_kwargs()

        assert kwargs == {'host': 'test-host', 'port': 8080, 'password': 'secret'}

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_get_client_kwargs_no_password(self):
        """Test get_client_kwargs without password."""
        config = FalkorDBConfig(host='test-host', port=8080)

        kwargs = config.get_client_kwargs()

        assert kwargs == {'host': 'test-host', 'port': 8080}

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_get_database_name(self):
        """Test get_database_name method."""
        # Default database (0) should return 'default_db'
        config = FalkorDBConfig(database=0)
        assert config.get_database_name() == 'default_db'

        # Other database numbers should return as strings
        config = FalkorDBConfig(database=5)
        assert config.get_database_name() == '5'

        config = FalkorDBConfig(database=123)
        assert config.get_database_name() == '123'


class TestFalkorDriverWithConfig:
    """Test FalkorDriver integration with FalkorDBConfig."""

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    def test_driver_init_with_direct_config(self, mock_falkor_db_class):
        """Test FalkorDriver initialization with FalkorDBConfig."""
        config = FalkorDBConfig(
            host='config-host', port=7000, database=3, password='config-password'
        )

        driver = FalkorDriver(config=config)

        mock_falkor_db_class.assert_called_once_with(
            host='config-host', port=7000, password='config-password'
        )
        assert driver._database == '3'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    @patch.dict(
        os.environ,
        {
            'FALKORDB_HOST': 'env-host',
            'FALKORDB_PORT': '8000',
            'FALKORDB_DATABASE': '5',
            'FALKORDB_PASSWORD': 'env-password',
        },
    )
    def test_driver_init_from_environment(self, mock_falkor_db_class):
        """Test FalkorDriver initialization from environment variables."""
        driver = FalkorDriver()

        mock_falkor_db_class.assert_called_once_with(
            host='env-host', port=8000, password='env-password'
        )
        assert driver._database == '5'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    @patch.dict(
        os.environ,
        {'FALKORDB_CONNECTION_STRING': 'redis://:conn-password@conn-host:9000/7'},
    )
    def test_driver_init_from_connection_string(self, mock_falkor_db_class):
        """Test FalkorDriver initialization from connection string."""
        driver = FalkorDriver()

        mock_falkor_db_class.assert_called_once_with(
            host='conn-host', port=9000, password='conn-password'
        )
        assert driver._database == '7'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    def test_driver_parameter_precedence(self, mock_falkor_db_class):
        """Test that direct parameters override config and environment."""
        config = FalkorDBConfig(
            host='config-host', port=7000, database=3, password='config-password'
        )

        with patch.dict(
            os.environ,
            {'FALKORDB_HOST': 'env-host', 'FALKORDB_PASSWORD': 'env-password'},
        ):
            driver = FalkorDriver(
                host='direct-host',
                port=8888,
                password='direct-password',
                database='direct-db',
                config=config,
            )

        # Direct parameters should take precedence
        mock_falkor_db_class.assert_called_once_with(
            host='direct-host', port=8888, password='direct-password'
        )
        assert driver._database == 'direct-db'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    @patch.dict(os.environ, {}, clear=True)
    def test_driver_defaults_when_no_config(self, mock_falkor_db_class):
        """Test FalkorDriver uses defaults when no config is provided."""
        driver = FalkorDriver()

        mock_falkor_db_class.assert_called_once_with(host='localhost', port=6379)
        assert driver._database == 'default_db'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_driver_with_falkor_db_instance(self):
        """Test FalkorDriver with pre-configured FalkorDB instance."""
        mock_falkor_db = MagicMock()

        driver = FalkorDriver(falkor_db=mock_falkor_db, database='custom-db')

        assert driver.client is mock_falkor_db
        assert driver._database == 'custom-db'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    def test_driver_legacy_username_parameter(self, mock_falkor_db_class):
        """Test FalkorDriver supports legacy username parameter."""
        FalkorDriver(username='legacy-user')

        # username should be used as password when no password is provided
        mock_falkor_db_class.assert_called_once_with(
            host='localhost', port=6379, password='legacy-user'
        )

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    def test_driver_password_overrides_username(self, mock_falkor_db_class):
        """Test that password parameter overrides username."""
        FalkorDriver(username='legacy-user', password='actual-password')

        mock_falkor_db_class.assert_called_once_with(
            host='localhost', port=6379, password='actual-password'
        )

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDBConfig.from_env')
    def test_driver_handles_config_loading_errors(self, mock_from_env):
        """Test FalkorDriver handles configuration loading errors gracefully."""
        mock_from_env.side_effect = ValueError('Invalid environment configuration')

        with pytest.raises(ValueError, match='Failed to load FalkorDB configuration'):
            FalkorDriver()

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    def test_driver_clone_method(self, mock_falkor_db_class):
        """Test FalkorDriver clone method with new configuration."""
        mock_falkor_db = MagicMock()
        mock_falkor_db_class.return_value = mock_falkor_db

        original_driver = FalkorDriver()
        cloned_driver = original_driver.clone('new-database')

        assert cloned_driver.client is original_driver.client  # Same client instance
        assert cloned_driver._database == 'new-database'  # Different database
        assert original_driver._database == 'default_db'  # Original unchanged


class TestFalkorDBConfigIntegration:
    """Integration tests for FalkorDB configuration scenarios."""

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch.dict(
        os.environ,
        {
            'FALKORDB_HOST': 'integration-host',
            'FALKORDB_PORT': '6380',
            'FALKORDB_DATABASE': '1',
            'FALKORDB_PASSWORD': 'integration-pass',
        },
    )
    def test_end_to_end_environment_config(self):
        """Test end-to-end configuration loading from environment."""
        config = FalkorDBConfig.from_env()

        assert config.host == 'integration-host'
        assert config.port == 6380
        assert config.database == 1
        assert config.password == 'integration-pass'

        kwargs = config.get_client_kwargs()
        assert kwargs['host'] == 'integration-host'
        assert kwargs['port'] == 6380
        assert kwargs['password'] == 'integration-pass'

        db_name = config.get_database_name()
        assert db_name == '1'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    def test_end_to_end_connection_string_config(self):
        """Test end-to-end configuration with connection string."""
        conn_str = 'redis://:secret@production-host:6379/10'
        config = FalkorDBConfig.from_connection_string(conn_str)

        assert config.host == 'production-host'
        assert config.port == 6379
        assert config.database == 10
        assert config.password == 'secret'

        kwargs = config.get_client_kwargs()
        assert kwargs['host'] == 'production-host'
        assert kwargs['port'] == 6379
        assert kwargs['password'] == 'secret'

        db_name = config.get_database_name()
        assert db_name == '10'

    @unittest.skipIf(not HAS_FALKORDB, 'FalkorDB is not installed')
    @patch('graphiti_core.driver.falkordb_driver.FalkorDB')
    def test_configuration_hierarchy_complex(self, mock_falkor_db_class):
        """Test complex configuration hierarchy with multiple override levels."""
        # Environment variables (lowest precedence)
        env_vars = {
            'FALKORDB_HOST': 'env-host',
            'FALKORDB_PORT': '7777',
            'FALKORDB_DATABASE': '2',
            'FALKORDB_PASSWORD': 'env-password',
        }

        # Config object (middle precedence)
        config = FalkorDBConfig(
            host='config-host', port=8888, database=5, password='config-password'
        )

        # Direct parameters (highest precedence)
        with patch.dict(os.environ, env_vars):
            driver = FalkorDriver(
                host='direct-host',  # Should win
                # port not provided, should use config value
                password='direct-password',  # Should win
                # database not provided, should use config value
                config=config,
            )

        mock_falkor_db_class.assert_called_once_with(
            host='direct-host',  # From direct parameter
            port=8888,  # From config object
            password='direct-password',  # From direct parameter
        )
        assert driver._database == '5'  # From config object
