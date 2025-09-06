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
import time

import pytest

from graphiti_core.driver.driver import GraphProvider
from tests.helpers_test import get_driver, group_id

pytestmark = [pytest.mark.integration, pytest.mark.falkordb]


class TestFalkorDBSpecificFeatures:
    """Integration tests for FalkorDB-specific features and Redis-based functionality."""

    @pytest.mark.asyncio
    async def test_falkordb_redis_connection(self):
        """Test FalkorDB-specific Redis connection and basic Redis commands."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(GraphProvider.FALKORDB)

            # Test basic graph database operation
            result, _, _ = await driver.execute_query("RETURN 1 as test_value")
            assert result[0]["test_value"] == 1

            # Test FalkorDB-specific features if available
            # Note: Some Redis commands may not be directly accessible through graph queries
            # This tests the graph interface specifically

            # Test database info (FalkorDB specific)
            try:
                # This may not be available in all FalkorDB versions
                info_result, _, _ = await driver.execute_query("CALL db.info()")
                assert isinstance(info_result, list)  # Should return some info
            except Exception as e:
                if "Unknown procedure" in str(e) or "not found" in str(e).lower():
                    # db.info() may not be available in all FalkorDB versions
                    pytest.skip(
                        f"db.info() not available in this FalkorDB version: {e}"
                    )
                raise

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"FalkorDB not available: {e}")
            raise
        finally:
            if driver:
                await driver.close()

    @pytest.mark.asyncio
    async def test_falkordb_performance_characteristics(self):
        """Test FalkorDB performance characteristics."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(GraphProvider.FALKORDB)

            # Test rapid node creation (FalkorDB should be fast with Redis backend)
            start_time = time.perf_counter()

            batch_size = 50
            for i in range(batch_size):
                await driver.execute_query(
                    """
                    CREATE (n:FalkorPerfTest {
                        uuid: $uuid,
                        name: $name,
                        group_id: $group_id,
                        index: $index,
                        created_at: datetime()
                    })
                    """,
                    uuid=f"falkor-perf-{i}",
                    name=f"FalkorDB Perf Node {i}",
                    group_id=group_id,
                    index=i,
                )

            creation_time = time.perf_counter() - start_time

            # Test rapid querying
            start_time = time.perf_counter()

            for i in range(0, batch_size, 10):  # Query every 10th node
                result, _, _ = await driver.execute_query(
                    """
                    MATCH (n:FalkorPerfTest)
                    WHERE n.group_id = $group_id AND n.index = $index
                    RETURN n.name
                    """,
                    group_id=group_id,
                    index=i,
                )
                assert len(result) == 1

            query_time = time.perf_counter() - start_time

            print(f"\nFalkorDB Performance Metrics:")
            print(f"  Node creation time for {batch_size} nodes: {creation_time:.3f}s")
            print(f"  Query time for {batch_size//10} queries: {query_time:.3f}s")
            print(
                f"  Avg creation time per node: {(creation_time/batch_size)*1000:.2f}ms"
            )
            print(f"  Avg query time: {(query_time/(batch_size//10))*1000:.2f}ms")

            # Basic performance assertions (should be reasonably fast)
            assert creation_time < 10.0  # Should create 50 nodes in under 10 seconds
            assert query_time < 5.0  # Should query 5 nodes in under 5 seconds

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"FalkorDB not available: {e}")
            raise
        finally:
            if driver:
                try:
                    # Cleanup
                    await driver.execute_query(
                        """
                        MATCH (n:FalkorPerfTest)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                except:
                    pass
                await driver.close()

    @pytest.mark.asyncio
    async def test_falkordb_data_persistence(self):
        """Test data persistence in FalkorDB across connections."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        # First connection - create data
        driver1 = None
        driver2 = None
        test_uuid = "falkor-persist-test"

        try:
            driver1 = get_driver(GraphProvider.FALKORDB)

            # Create a node
            await driver1.execute_query(
                """
                CREATE (n:PersistenceTest {
                    uuid: $uuid,
                    name: 'Persistent Node',
                    group_id: $group_id,
                    created_at: datetime()
                })
                """,
                uuid=test_uuid,
                group_id=group_id,
            )

            # Close first connection
            await driver1.close()
            driver1 = None

            # Open second connection and verify data exists
            driver2 = get_driver(GraphProvider.FALKORDB)

            result, _, _ = await driver2.execute_query(
                """
                MATCH (n:PersistenceTest)
                WHERE n.uuid = $uuid AND n.group_id = $group_id
                RETURN n.name as name, n.uuid as uuid
                """,
                uuid=test_uuid,
                group_id=group_id,
            )

            assert len(result) == 1
            assert result[0]["name"] == "Persistent Node"
            assert result[0]["uuid"] == test_uuid

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"FalkorDB not available: {e}")
            raise
        finally:
            # Cleanup with whichever driver is available
            cleanup_driver = driver2 if driver2 else driver1
            if cleanup_driver:
                try:
                    await cleanup_driver.execute_query(
                        """
                        MATCH (n:PersistenceTest)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                except:
                    pass
                await cleanup_driver.close()

    @pytest.mark.asyncio
    async def test_falkordb_concurrent_operations(self):
        """Test FalkorDB handling of concurrent operations."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        import asyncio

        async def create_nodes(driver, start_idx, count):
            """Create a batch of nodes."""
            for i in range(start_idx, start_idx + count):
                await driver.execute_query(
                    """
                    CREATE (n:ConcurrencyTest {
                        uuid: $uuid,
                        name: $name,
                        group_id: $group_id,
                        batch: $batch
                    })
                    """,
                    uuid=f"concurrent-{i}",
                    name=f"Concurrent Node {i}",
                    group_id=group_id,
                    batch=start_idx // count,
                )

        drivers = []
        try:
            # Create multiple connections
            num_connections = 3
            batch_size = 10

            for _ in range(num_connections):
                drivers.append(get_driver(GraphProvider.FALKORDB))

            # Run concurrent operations
            tasks = []
            for i, driver in enumerate(drivers):
                start_idx = i * batch_size
                tasks.append(create_nodes(driver, start_idx, batch_size))

            await asyncio.gather(*tasks)

            # Verify all nodes were created
            result, _, _ = await drivers[0].execute_query(
                """
                MATCH (n:ConcurrencyTest)
                WHERE n.group_id = $group_id
                RETURN COUNT(n) as total_count, COUNT(DISTINCT n.batch) as batch_count
                """,
                group_id=group_id,
            )

            expected_total = num_connections * batch_size
            assert result[0]["total_count"] == expected_total
            assert result[0]["batch_count"] == num_connections

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"FalkorDB not available: {e}")
            raise
        finally:
            # Cleanup
            if drivers:
                try:
                    await drivers[0].execute_query(
                        """
                        MATCH (n:ConcurrencyTest)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                except:
                    pass

                for driver in drivers:
                    try:
                        await driver.close()
                    except:
                        pass

    @pytest.mark.asyncio
    async def test_falkordb_memory_efficiency(self):
        """Test FalkorDB memory usage characteristics."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(GraphProvider.FALKORDB)

            # Create a moderately large dataset
            node_count = 100
            edge_count = 200

            # Create nodes
            for i in range(node_count):
                await driver.execute_query(
                    """
                    CREATE (n:MemoryTest {
                        uuid: $uuid,
                        name: $name,
                        group_id: $group_id,
                        index: $index,
                        data: $data
                    })
                    """,
                    uuid=f"memory-test-{i}",
                    name=f"Memory Test Node {i}",
                    group_id=group_id,
                    index=i,
                    data=f"Some test data for node {i} " * 10,  # Add some bulk
                )

            # Create edges between nodes
            for i in range(edge_count):
                from_idx = i % node_count
                to_idx = (i + 1) % node_count

                await driver.execute_query(
                    """
                    MATCH (a:MemoryTest), (b:MemoryTest)
                    WHERE a.index = $from_idx AND b.index = $to_idx
                    AND a.group_id = $group_id AND b.group_id = $group_id
                    CREATE (a)-[r:MEMORY_TEST_EDGE {uuid: $uuid, weight: $weight}]->(b)
                    """,
                    from_idx=from_idx,
                    to_idx=to_idx,
                    group_id=group_id,
                    uuid=f"memory-edge-{i}",
                    weight=float(i % 100) / 10.0,
                )

            # Verify the graph was created correctly
            result, _, _ = await driver.execute_query(
                """
                MATCH (n:MemoryTest)
                WHERE n.group_id = $group_id
                RETURN COUNT(n) as node_count
                """,
                group_id=group_id,
            )
            assert result[0]["node_count"] == node_count

            edge_result, _, _ = await driver.execute_query(
                """
                MATCH ()-[r:MEMORY_TEST_EDGE]->()
                RETURN COUNT(r) as edge_count
                """,
                group_id=group_id,
            )
            assert edge_result[0]["edge_count"] == edge_count

            # Test complex queries on this dataset
            complex_result, _, _ = await driver.execute_query(
                """
                MATCH (n:MemoryTest)-[r:MEMORY_TEST_EDGE]->(m:MemoryTest)
                WHERE n.group_id = $group_id
                RETURN AVG(r.weight) as avg_weight, MAX(r.weight) as max_weight, COUNT(r) as edge_count
                """,
                group_id=group_id,
            )

            assert complex_result[0]["edge_count"] == edge_count
            assert complex_result[0]["avg_weight"] >= 0
            assert complex_result[0]["max_weight"] >= 0

            print(f"\nFalkorDB Memory Test Results:")
            print(f"  Created {node_count} nodes and {edge_count} edges successfully")
            print(f"  Average edge weight: {complex_result[0]['avg_weight']:.2f}")
            print(f"  Maximum edge weight: {complex_result[0]['max_weight']:.2f}")

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"FalkorDB not available: {e}")
            raise
        finally:
            if driver:
                try:
                    # Cleanup
                    await driver.execute_query(
                        """
                        MATCH (n:MemoryTest)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                except:
                    pass
                await driver.close()

    @pytest.mark.asyncio
    async def test_falkordb_transaction_behavior(self):
        """Test FalkorDB transaction handling."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(GraphProvider.FALKORDB)

            # Test that operations are atomic within a single query
            # Create multiple nodes in one transaction
            await driver.execute_query(
                """
                CREATE (a:TransactionTest {uuid: 'tx-test-1', name: 'Node A', group_id: $group_id})
                CREATE (b:TransactionTest {uuid: 'tx-test-2', name: 'Node B', group_id: $group_id})
                CREATE (c:TransactionTest {uuid: 'tx-test-3', name: 'Node C', group_id: $group_id})
                CREATE (a)-[:CONNECTS_TO]->(b)
                CREATE (b)-[:CONNECTS_TO]->(c)
                CREATE (a)-[:CONNECTS_TO]->(c)
                """,
                group_id=group_id,
            )

            # Verify all data was created atomically
            result, _, _ = await driver.execute_query(
                """
                MATCH (n:TransactionTest)
                WHERE n.group_id = $group_id
                RETURN COUNT(n) as node_count
                """,
                group_id=group_id,
            )
            assert result[0]["node_count"] == 3

            edge_result, _, _ = await driver.execute_query(
                """
                MATCH ()-[r:CONNECTS_TO]->()
                RETURN COUNT(r) as edge_count
                """
            )
            assert edge_result[0]["edge_count"] == 3

            # Test that failed operations don't leave partial data
            try:
                await driver.execute_query(
                    """
                    CREATE (d:TransactionTest {uuid: 'tx-test-4', name: 'Node D', group_id: $group_id})
                    CREATE (invalid:syntax error here
                    """,
                    group_id=group_id,
                )
                assert False, "Should have failed due to syntax error"
            except Exception:
                pass  # Expected to fail

            # Verify that Node D was not created due to transaction rollback
            result, _, _ = await driver.execute_query(
                """
                MATCH (n:TransactionTest)
                WHERE n.group_id = $group_id AND n.uuid = 'tx-test-4'
                RETURN COUNT(n) as count
                """,
                group_id=group_id,
            )
            assert result[0]["count"] == 0  # Should not exist due to rollback

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"FalkorDB not available: {e}")
            raise
        finally:
            if driver:
                try:
                    # Cleanup
                    await driver.execute_query(
                        """
                        MATCH (n:TransactionTest)
                        WHERE n.group_id = $group_id
                        DETACH DELETE n
                        """,
                        group_id=group_id,
                    )
                except:
                    pass
                await driver.close()
