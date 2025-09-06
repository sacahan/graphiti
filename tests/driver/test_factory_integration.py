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
import sys
from unittest.mock import patch

import pytest

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.driver.factory import DriverFactory
from tests.helpers_test import get_driver, group_id

pytestmark = pytest.mark.integration


class TestDriverFactoryIntegration:
    """Integration tests for DriverFactory with real database connections."""

    @pytest.mark.asyncio
    async def test_create_driver_neo4j_integration(self):
        """Test creating and connecting to Neo4j driver through factory."""
        if os.getenv("DISABLE_NEO4J"):
            pytest.skip("Neo4j disabled for this test run")

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "test")

        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"}):
            driver = DriverFactory.create_driver(
                uri=neo4j_uri, user=neo4j_user, password=neo4j_password
            )

        # Test basic connectivity and operations
        assert driver.provider == GraphProvider.NEO4J

        try:
            # Test basic query execution
            result, _, _ = await driver.execute_query(
                "RETURN 1 as test_value",
            )
            assert result[0]["test_value"] == 1

            # Test database creation and connection
            if hasattr(driver, "database"):
                # Ensure we can work with the database
                result, _, _ = await driver.execute_query(
                    "MATCH (n) RETURN COUNT(n) as node_count LIMIT 1",
                )
                assert "node_count" in result[0]
        finally:
            await driver.close()

    @pytest.mark.asyncio
    async def test_create_driver_falkordb_integration(self):
        """Test creating and connecting to FalkorDB driver through factory."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        falkordb_host = os.getenv("FALKORDB_HOST", "localhost")
        falkordb_port = os.getenv("FALKORDB_PORT", "6379")

        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "falkordb"}):
            driver = DriverFactory.create_driver()

        # Test basic connectivity and operations
        assert driver.provider == GraphProvider.FALKORDB

        try:
            # Test basic query execution
            result, _, _ = await driver.execute_query(
                "RETURN 1 as test_value",
            )
            assert result[0]["test_value"] == 1

            # Test database selection
            if hasattr(driver, "database"):
                # Ensure we can work with the database
                result, _, _ = await driver.execute_query(
                    "MATCH (n) RETURN COUNT(n) as node_count",
                )
                assert "node_count" in result[0]
        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"FalkorDB not available: {e}")
            raise
        finally:
            await driver.close()

    @pytest.mark.asyncio
    async def test_database_switching_functionality(self):
        """Test switching between database types via environment variable."""
        if os.getenv("DISABLE_NEO4J") or os.getenv("DISABLE_FALKORDB"):
            pytest.skip("Both Neo4j and FalkorDB needed for switching test")

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "test")

        # Test Neo4j
        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"}):
            neo4j_driver = DriverFactory.create_driver(
                uri=neo4j_uri, user=neo4j_user, password=neo4j_password
            )
            assert neo4j_driver.provider == GraphProvider.NEO4J

        # Test FalkorDB
        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "falkordb"}):
            falkor_driver = DriverFactory.create_driver()
            assert falkor_driver.provider == GraphProvider.FALKORDB

        # Cleanup
        try:
            await neo4j_driver.close()
        except:
            pass
        try:
            await falkor_driver.close()
        except:
            pass

    @pytest.mark.asyncio
    async def test_driver_factory_with_custom_database_name(self):
        """Test DriverFactory can create drivers with custom database names."""
        if os.getenv("DISABLE_NEO4J"):
            pytest.skip("Neo4j disabled for this test run")

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "test")
        custom_db = "test_custom_db"

        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"}):
            driver = DriverFactory.create_driver(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password,
                database=custom_db,
            )

        try:
            # The database parameter should be passed through
            # Note: In real Neo4j, the database might need to exist
            # This tests the parameter passing, not necessarily connection
            assert driver.provider == GraphProvider.NEO4J

            # For FalkorDB test
            if not os.getenv("DISABLE_FALKORDB"):
                with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "falkordb"}):
                    falkor_driver = DriverFactory.create_driver(database=custom_db)
                    assert falkor_driver.provider == GraphProvider.FALKORDB
                    await falkor_driver.close()

        except Exception as e:
            if "database" in str(e).lower() and (
                "not found" in str(e).lower() or "does not exist" in str(e).lower()
            ):
                # This is expected - custom database may not exist
                pytest.skip(f"Custom database doesn't exist (expected): {e}")
            elif "Connection refused" in str(e):
                pytest.skip(f"Database not available: {e}")
            else:
                raise
        finally:
            await driver.close()

    @pytest.mark.asyncio
    async def test_driver_compatibility_with_graphiti_core(self):
        """Test that factory-created drivers work with core Graphiti operations."""
        if os.getenv("DISABLE_NEO4J") and os.getenv("DISABLE_FALKORDB"):
            pytest.skip("At least one database backend needed")

        # Test with available database
        if not os.getenv("DISABLE_NEO4J"):
            provider = GraphProvider.NEO4J
        else:
            provider = GraphProvider.FALKORDB

        driver = get_driver(provider)

        try:
            # Clear any existing test data
            await driver.execute_query(
                """
                MATCH (n)
                WHERE n.group_id = $group_id
                DETACH DELETE n
                """,
                group_id=group_id,
            )

            # Test basic node creation (minimal Graphiti operation)
            await driver.execute_query(
                """
                CREATE (n:TestNode {
                    uuid: $uuid,
                    name: $name,
                    group_id: $group_id,
                    created_at: datetime()
                })
                """,
                uuid="test-node-001",
                name="Test Node",
                group_id=group_id,
            )

            # Verify node exists
            result, _, _ = await driver.execute_query(
                """
                MATCH (n:TestNode)
                WHERE n.group_id = $group_id AND n.uuid = $uuid
                RETURN n.name as name, n.uuid as uuid
                """,
                group_id=group_id,
                uuid="test-node-001",
            )

            assert len(result) == 1
            assert result[0]["name"] == "Test Node"
            assert result[0]["uuid"] == "test-node-001"

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"Database not available: {e}")
            raise
        finally:
            # Cleanup
            try:
                await driver.execute_query(
                    """
                    MATCH (n)
                    WHERE n.group_id = $group_id
                    DETACH DELETE n
                    """,
                    group_id=group_id,
                )
            except:
                pass
            await driver.close()

    @pytest.mark.asyncio
    async def test_driver_error_handling_integration(self):
        """Test error handling in factory-created drivers."""

        # Test invalid database type
        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "invalid_db"}):
            with pytest.raises(
                ValueError, match="Unsupported database type: invalid_db"
            ):
                DriverFactory.create_driver()

        # Test Neo4j without URI
        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"}):
            with pytest.raises(
                ValueError, match="uri must be provided when using Neo4j driver"
            ):
                DriverFactory.create_driver(uri=None)

        # Test connection errors are properly propagated
        with patch.dict(os.environ, {"GRAPHITI_DB_TYPE": "neo4j"}):
            driver = DriverFactory.create_driver(
                uri="bolt://nonexistent:7687", user="test", password="test"
            )

            with pytest.raises(Exception) as exc_info:
                await driver.execute_query("RETURN 1")

            # Should get a connection-related error
            error_message = str(exc_info.value).lower()
            assert any(
                keyword in error_message
                for keyword in [
                    "connection",
                    "refused",
                    "timeout",
                    "unreachable",
                    "resolve",
                ]
            )

            await driver.close()
