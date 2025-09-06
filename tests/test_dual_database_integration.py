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
from unittest.mock import Mock

import pytest

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.graphiti import Graphiti
from tests.helpers_test import get_driver, group_id, mock_embedder

pytestmark = [pytest.mark.integration, pytest.mark.dual_database]


class TestDualDatabaseIntegration:
    """Integration tests to ensure both Neo4j and FalkorDB work correctly."""

    @pytest.mark.parametrize("provider", [GraphProvider.NEO4J, GraphProvider.FALKORDB])
    @pytest.mark.asyncio
    async def test_basic_database_operations(self, provider):
        """Test basic database operations work on both backends."""
        if provider == GraphProvider.NEO4J and os.getenv("DISABLE_NEO4J"):
            pytest.skip("Neo4j disabled for this test run")
        if provider == GraphProvider.FALKORDB and os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(provider)

            # Test basic connectivity
            result, _, _ = await driver.execute_query("RETURN 1 as test_value")
            assert result[0]["test_value"] == 1

            # Test node creation and retrieval
            await driver.execute_query(
                """
                CREATE (n:TestNode {
                    uuid: $uuid,
                    name: $name,
                    group_id: $group_id,
                    created_at: datetime()
                })
                """,
                uuid=f"test-{provider.value}-001",
                name=f"Test Node for {provider.value}",
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
                uuid=f"test-{provider.value}-001",
            )

            assert len(result) == 1
            assert result[0]["name"] == f"Test Node for {provider.value}"
            assert result[0]["uuid"] == f"test-{provider.value}-001"

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"{provider.value} not available: {e}")
            raise
        finally:
            # Cleanup
            if driver:
                try:
                    await driver.execute_query(
                        """
                        MATCH (n:TestNode)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                except:
                    pass
                await driver.close()

    @pytest.mark.parametrize("provider", [GraphProvider.NEO4J, GraphProvider.FALKORDB])
    @pytest.mark.asyncio
    async def test_graphiti_initialization_with_database(self, provider, mock_embedder):
        """Test that Graphiti can be initialized with both database backends."""
        if provider == GraphProvider.NEO4J and os.getenv("DISABLE_NEO4J"):
            pytest.skip("Neo4j disabled for this test run")
        if provider == GraphProvider.FALKORDB and os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        # Skip if no OpenAI API key is available (required for LLM client)
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key required for Graphiti initialization")

        driver = None
        graphiti = None
        try:
            driver = get_driver(provider)

            # Initialize Graphiti with the specific driver
            graphiti = Graphiti(
                graph_driver=driver,
                embedder_client=mock_embedder,  # Use mock to avoid API calls
            )

            # Test that we can build indices without errors
            await graphiti.build_indices_and_constraints()

            # Test basic search (should return empty results but not error)
            results = await graphiti.search_(query="test query")
            assert isinstance(results, list)  # Should return a list, even if empty

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"{provider.value} not available: {e}")
            elif "api_key" in str(e).lower():
                pytest.skip(f"API key required: {e}")
            raise
        finally:
            if graphiti:
                await graphiti.close()
            elif driver:
                await driver.close()

    @pytest.mark.asyncio
    async def test_database_switching_integration(self):
        """Test switching between databases in the same test session."""
        if os.getenv("DISABLE_NEO4J") or os.getenv("DISABLE_FALKORDB"):
            pytest.skip("Both Neo4j and FalkorDB needed for switching test")

        neo4j_driver = None
        falkor_driver = None

        try:
            # Test Neo4j operations
            neo4j_driver = get_driver(GraphProvider.NEO4J)
            await neo4j_driver.execute_query(
                """
                CREATE (n:SwitchTest {
                    uuid: $uuid,
                    database: 'neo4j',
                    group_id: $group_id
                })
                """,
                uuid="switch-test-neo4j",
                group_id=group_id,
            )

            # Test FalkorDB operations
            falkor_driver = get_driver(GraphProvider.FALKORDB)
            await falkor_driver.execute_query(
                """
                CREATE (n:SwitchTest {
                    uuid: $uuid,
                    database: 'falkordb',
                    group_id: $group_id
                })
                """,
                uuid="switch-test-falkor",
                group_id=group_id,
            )

            # Verify each database has its own data
            neo4j_result, _, _ = await neo4j_driver.execute_query(
                """
                MATCH (n:SwitchTest)
                WHERE n.group_id = $group_id
                RETURN n.database as db, COUNT(n) as count
                """,
                group_id=group_id,
            )

            falkor_result, _, _ = await falkor_driver.execute_query(
                """
                MATCH (n:SwitchTest)
                WHERE n.group_id = $group_id  
                RETURN n.database as db, COUNT(n) as count
                """,
                group_id=group_id,
            )

            # Each database should have its own data
            assert neo4j_result[0]["db"] == "neo4j"
            assert falkor_result[0]["db"] == "falkordb"
            assert neo4j_result[0]["count"] == 1
            assert falkor_result[0]["count"] == 1

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"Database not available: {e}")
            raise
        finally:
            # Cleanup both databases
            if neo4j_driver:
                try:
                    await neo4j_driver.execute_query(
                        "MATCH (n:SwitchTest) WHERE n.group_id = $group_id DETACH DELETE n",
                        group_id=group_id,
                    )
                except:
                    pass
                await neo4j_driver.close()
            if falkor_driver:
                try:
                    await falkor_driver.execute_query(
                        "MATCH (n:SwitchTest) WHERE n.group_id = $group_id DETACH DELETE n",
                        group_id=group_id,
                    )
                except:
                    pass
                await falkor_driver.close()

    @pytest.mark.parametrize("provider", [GraphProvider.NEO4J, GraphProvider.FALKORDB])
    @pytest.mark.asyncio
    async def test_database_constraints_and_indices(self, provider):
        """Test that both databases support constraints and indices creation."""
        if provider == GraphProvider.NEO4J and os.getenv("DISABLE_NEO4J"):
            pytest.skip("Neo4j disabled for this test run")
        if provider == GraphProvider.FALKORDB and os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(provider)

            # Create a simple index (syntax may vary between databases)
            try:
                # Try Neo4j syntax first
                await driver.execute_query(
                    "CREATE INDEX test_index_name IF NOT EXISTS FOR (n:TestIndexNode) ON (n.name)"
                )
            except Exception:
                try:
                    # Try alternative syntax
                    await driver.execute_query("CREATE INDEX ON :TestIndexNode(name)")
                except Exception as e:
                    # Some databases might not support indices in the same way
                    if "syntax" in str(e).lower() or "not supported" in str(e).lower():
                        pytest.skip(
                            f"Index creation not supported on {provider.value}: {e}"
                        )
                    raise

            # Test that we can create nodes and they work with indices
            await driver.execute_query(
                """
                CREATE (n:TestIndexNode {
                    name: $name,
                    group_id: $group_id,
                    uuid: $uuid
                })
                """,
                name=f"indexed_node_{provider.value}",
                group_id=group_id,
                uuid=f"indexed-{provider.value}",
            )

            # Query using the indexed field
            result, _, _ = await driver.execute_query(
                """
                MATCH (n:TestIndexNode)
                WHERE n.name = $name AND n.group_id = $group_id
                RETURN n.uuid as uuid
                """,
                name=f"indexed_node_{provider.value}",
                group_id=group_id,
            )

            assert len(result) == 1
            assert result[0]["uuid"] == f"indexed-{provider.value}"

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"{provider.value} not available: {e}")
            raise
        finally:
            if driver:
                try:
                    # Cleanup
                    await driver.execute_query(
                        """
                        MATCH (n:TestIndexNode)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                    # Try to drop index (may fail, that's OK)
                    try:
                        await driver.execute_query(
                            "DROP INDEX test_index_name IF EXISTS"
                        )
                    except:
                        pass
                except:
                    pass
                await driver.close()

    @pytest.mark.parametrize("provider", [GraphProvider.NEO4J, GraphProvider.FALKORDB])
    @pytest.mark.asyncio
    async def test_complex_cypher_queries(self, provider):
        """Test complex Cypher queries work on both backends."""
        if provider == GraphProvider.NEO4J and os.getenv("DISABLE_NEO4J"):
            pytest.skip("Neo4j disabled for this test run")
        if provider == GraphProvider.FALKORDB and os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(provider)

            # Create a small graph for testing
            await driver.execute_query(
                """
                CREATE (a:ComplexTestNode {name: 'A', group_id: $group_id, uuid: 'complex-a'})
                CREATE (b:ComplexTestNode {name: 'B', group_id: $group_id, uuid: 'complex-b'})  
                CREATE (c:ComplexTestNode {name: 'C', group_id: $group_id, uuid: 'complex-c'})
                CREATE (a)-[:CONNECTS_TO {weight: 1.0}]->(b)
                CREATE (b)-[:CONNECTS_TO {weight: 2.0}]->(c)
                CREATE (a)-[:CONNECTS_TO {weight: 3.0}]->(c)
                """,
                group_id=group_id,
            )

            # Test complex query with aggregation and ordering
            result, _, _ = await driver.execute_query(
                """
                MATCH (a:ComplexTestNode)-[r:CONNECTS_TO]->(b:ComplexTestNode)
                WHERE a.group_id = $group_id
                RETURN a.name as source, b.name as target, r.weight as weight
                ORDER BY r.weight DESC
                """,
                group_id=group_id,
            )

            assert len(result) == 3
            # Should be ordered by weight descending
            assert result[0]["weight"] == 3.0
            assert result[0]["source"] == "A"
            assert result[0]["target"] == "C"

            # Test aggregation query
            agg_result, _, _ = await driver.execute_query(
                """
                MATCH (n:ComplexTestNode)
                WHERE n.group_id = $group_id
                RETURN COUNT(n) as node_count, AVG(3.0) as avg_test
                """,
                group_id=group_id,
            )

            assert agg_result[0]["node_count"] == 3
            assert agg_result[0]["avg_test"] == 3.0

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"{provider.value} not available: {e}")
            raise
        finally:
            if driver:
                try:
                    # Cleanup
                    await driver.execute_query(
                        """
                        MATCH (n:ComplexTestNode)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                except:
                    pass
                await driver.close()
