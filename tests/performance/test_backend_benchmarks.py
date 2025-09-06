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

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
import statistics

import psutil
import pytest

from graphiti_core.driver.driver import GraphDriver, GraphProvider
from tests.helpers_test import get_driver, group_id

pytestmark = [pytest.mark.integration, pytest.mark.performance]


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    operation: str
    database: str
    duration_ms: float
    memory_mb: float
    success: bool
    error: Optional[str] = None


@dataclass
class BenchmarkSummary:
    """Summary of benchmark results."""

    database: str
    total_operations: int
    successful_operations: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    avg_memory_mb: float
    errors: List[str]


class DatabaseBenchmark:
    """Performance benchmark suite for database backends."""

    def __init__(self, driver: GraphDriver, database_name: str):
        self.driver = driver
        self.database_name = database_name
        self.results: List[BenchmarkResult] = []

    async def measure_operation(self, operation_name: str, operation_func):
        """Measure the performance of a database operation."""
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.perf_counter()
        success = True
        error = None

        try:
            await operation_func()
        except Exception as e:
            success = False
            error = str(e)

        end_time = time.perf_counter()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB

        duration_ms = (end_time - start_time) * 1000
        memory_delta = memory_after - memory_before

        result = BenchmarkResult(
            operation=operation_name,
            database=self.database_name,
            duration_ms=duration_ms,
            memory_mb=memory_delta,
            success=success,
            error=error,
        )

        self.results.append(result)
        return result

    async def benchmark_connection(self):
        """Benchmark database connection time."""

        async def connect_operation():
            # Connection is already established, just test a simple query
            await self.driver.execute_query("RETURN 1")

        return await self.measure_operation("connection_test", connect_operation)

    async def benchmark_node_creation(self, batch_size: int = 10):
        """Benchmark node creation performance."""

        async def create_nodes():
            for i in range(batch_size):
                await self.driver.execute_query(
                    """
                    CREATE (n:BenchmarkNode {
                        uuid: $uuid,
                        name: $name,
                        group_id: $group_id,
                        created_at: datetime(),
                        index: $index
                    })
                    """,
                    uuid=f"bench-node-{i}",
                    name=f"Benchmark Node {i}",
                    group_id=group_id,
                    index=i,
                )

        return await self.measure_operation(f"create_{batch_size}_nodes", create_nodes)

    async def benchmark_node_query(self, query_count: int = 10):
        """Benchmark node query performance."""

        async def query_nodes():
            for i in range(query_count):
                await self.driver.execute_query(
                    """
                    MATCH (n:BenchmarkNode)
                    WHERE n.group_id = $group_id AND n.index = $index
                    RETURN n.name
                    """,
                    group_id=group_id,
                    index=i % 5,  # Query for existing nodes
                )

        return await self.measure_operation(f"query_{query_count}_nodes", query_nodes)

    async def benchmark_edge_creation(self, edge_count: int = 10):
        """Benchmark edge creation performance."""

        async def create_edges():
            for i in range(edge_count):
                await self.driver.execute_query(
                    """
                    MATCH (a:BenchmarkNode), (b:BenchmarkNode)
                    WHERE a.index = $from_index AND b.index = $to_index
                    AND a.group_id = $group_id AND b.group_id = $group_id
                    CREATE (a)-[r:BENCHMARK_EDGE {
                        uuid: $uuid,
                        created_at: datetime()
                    }]->(b)
                    """,
                    from_index=i % 5,
                    to_index=(i + 1) % 5,
                    group_id=group_id,
                    uuid=f"bench-edge-{i}",
                )

        return await self.measure_operation(f"create_{edge_count}_edges", create_edges)

    async def benchmark_complex_query(self):
        """Benchmark complex query performance."""

        async def complex_query():
            await self.driver.execute_query(
                """
                MATCH (n:BenchmarkNode)-[r:BENCHMARK_EDGE]->(m:BenchmarkNode)
                WHERE n.group_id = $group_id
                RETURN n.name, r.uuid, m.name, COUNT(*) as path_count
                ORDER BY path_count DESC
                LIMIT 10
                """,
                group_id=group_id,
            )

        return await self.measure_operation("complex_query", complex_query)

    async def cleanup(self):
        """Clean up benchmark data."""

        async def cleanup_operation():
            await self.driver.execute_query(
                """
                MATCH (n:BenchmarkNode)
                WHERE n.group_id = $group_id
                DETACH DELETE n
                """,
                group_id=group_id,
            )

        await self.measure_operation("cleanup", cleanup_operation)

    def get_summary(self) -> BenchmarkSummary:
        """Get summary of benchmark results."""
        successful_results = [r for r in self.results if r.success]

        if not successful_results:
            return BenchmarkSummary(
                database=self.database_name,
                total_operations=len(self.results),
                successful_operations=0,
                avg_duration_ms=0.0,
                min_duration_ms=0.0,
                max_duration_ms=0.0,
                avg_memory_mb=0.0,
                errors=[r.error for r in self.results if r.error],
            )

        durations = [r.duration_ms for r in successful_results]
        memories = [r.memory_mb for r in successful_results]

        return BenchmarkSummary(
            database=self.database_name,
            total_operations=len(self.results),
            successful_operations=len(successful_results),
            avg_duration_ms=statistics.mean(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            avg_memory_mb=statistics.mean(memories),
            errors=[r.error for r in self.results if r.error],
        )


class TestDatabaseBenchmarks:
    """Integration tests for database performance benchmarks."""

    @pytest.mark.asyncio
    async def test_neo4j_performance_benchmark(self):
        """Benchmark Neo4j performance."""
        if os.getenv("DISABLE_NEO4J"):
            pytest.skip("Neo4j disabled for this test run")

        driver = None
        try:
            driver = get_driver(GraphProvider.NEO4J)
            benchmark = DatabaseBenchmark(driver, "Neo4j")

            # Run benchmarks
            await benchmark.benchmark_connection()
            await benchmark.benchmark_node_creation(batch_size=5)
            await benchmark.benchmark_node_query(query_count=5)
            await benchmark.benchmark_edge_creation(edge_count=5)
            await benchmark.benchmark_complex_query()
            await benchmark.cleanup()

            # Analyze results
            summary = benchmark.get_summary()
            assert summary.successful_operations > 0
            assert summary.avg_duration_ms > 0

            # Log results for analysis
            print(f"\nNeo4j Benchmark Results:")
            print(f"  Total operations: {summary.total_operations}")
            print(f"  Successful operations: {summary.successful_operations}")
            print(f"  Average duration: {summary.avg_duration_ms:.2f}ms")
            print(f"  Min duration: {summary.min_duration_ms:.2f}ms")
            print(f"  Max duration: {summary.max_duration_ms:.2f}ms")
            print(f"  Average memory delta: {summary.avg_memory_mb:.2f}MB")

            if summary.errors:
                print(f"  Errors: {summary.errors}")

        except Exception as e:
            if "Connection refused" in str(e):
                pytest.skip(f"Neo4j not available: {e}")
            raise
        finally:
            if driver:
                await driver.close()

    @pytest.mark.asyncio
    async def test_falkordb_performance_benchmark(self):
        """Benchmark FalkorDB performance."""
        if os.getenv("DISABLE_FALKORDB"):
            pytest.skip("FalkorDB disabled for this test run")

        driver = None
        try:
            driver = get_driver(GraphProvider.FALKORDB)
            benchmark = DatabaseBenchmark(driver, "FalkorDB")

            # Run benchmarks
            await benchmark.benchmark_connection()
            await benchmark.benchmark_node_creation(batch_size=5)
            await benchmark.benchmark_node_query(query_count=5)
            await benchmark.benchmark_edge_creation(edge_count=5)
            await benchmark.benchmark_complex_query()
            await benchmark.cleanup()

            # Analyze results
            summary = benchmark.get_summary()
            assert summary.successful_operations > 0
            assert summary.avg_duration_ms > 0

            # Log results for analysis
            print(f"\nFalkorDB Benchmark Results:")
            print(f"  Total operations: {summary.total_operations}")
            print(f"  Successful operations: {summary.successful_operations}")
            print(f"  Average duration: {summary.avg_duration_ms:.2f}ms")
            print(f"  Min duration: {summary.min_duration_ms:.2f}ms")
            print(f"  Max duration: {summary.max_duration_ms:.2f}ms")
            print(f"  Average memory delta: {summary.avg_memory_mb:.2f}MB")

            if summary.errors:
                print(f"  Errors: {summary.errors}")

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
    async def test_database_performance_comparison(self):
        """Compare performance between Neo4j and FalkorDB."""
        if os.getenv("DISABLE_NEO4J") or os.getenv("DISABLE_FALKORDB"):
            pytest.skip("Both Neo4j and FalkorDB needed for comparison")

        neo4j_driver = None
        falkor_driver = None
        benchmarks = {}

        try:
            # Benchmark Neo4j
            neo4j_driver = get_driver(GraphProvider.NEO4J)
            neo4j_benchmark = DatabaseBenchmark(neo4j_driver, "Neo4j")

            # Benchmark FalkorDB
            falkor_driver = get_driver(GraphProvider.FALKORDB)
            falkor_benchmark = DatabaseBenchmark(falkor_driver, "FalkorDB")

            # Run same benchmarks on both databases
            for benchmark in [neo4j_benchmark, falkor_benchmark]:
                await benchmark.benchmark_connection()
                await benchmark.benchmark_node_creation(batch_size=3)
                await benchmark.benchmark_node_query(query_count=3)
                await benchmark.benchmark_edge_creation(edge_count=3)
                await benchmark.cleanup()

                benchmarks[benchmark.database_name] = benchmark.get_summary()

            # Compare results
            neo4j_summary = benchmarks["Neo4j"]
            falkor_summary = benchmarks["FalkorDB"]

            print(f"\nPerformance Comparison:")
            print(f"Neo4j avg duration: {neo4j_summary.avg_duration_ms:.2f}ms")
            print(f"FalkorDB avg duration: {falkor_summary.avg_duration_ms:.2f}ms")

            # Performance regression check
            # Allow for some variance, but flag significant regressions
            performance_ratio = (
                falkor_summary.avg_duration_ms / neo4j_summary.avg_duration_ms
            )
            print(f"FalkorDB/Neo4j performance ratio: {performance_ratio:.2f}")

            # Both should have successful operations
            assert neo4j_summary.successful_operations > 0
            assert falkor_summary.successful_operations > 0

            # Log warning if there's a significant performance difference
            if performance_ratio > 2.0:
                print(
                    f"WARNING: FalkorDB appears significantly slower than Neo4j ({performance_ratio:.2f}x)"
                )
            elif performance_ratio < 0.5:
                print(
                    f"INFO: FalkorDB appears significantly faster than Neo4j ({performance_ratio:.2f}x)"
                )

        except Exception as e:
            if "Connection refused" in str(e) or "No connection could be made" in str(
                e
            ):
                pytest.skip(f"Database not available: {e}")
            raise
        finally:
            if neo4j_driver:
                await neo4j_driver.close()
            if falkor_driver:
                await falkor_driver.close()

    @pytest.mark.asyncio
    async def test_startup_time_benchmark(self):
        """Benchmark database startup/connection time."""
        startup_times = {}

        # Test Neo4j startup time
        if not os.getenv("DISABLE_NEO4J"):
            try:
                start_time = time.perf_counter()
                driver = get_driver(GraphProvider.NEO4J)
                # Test connection
                await driver.execute_query("RETURN 1")
                end_time = time.perf_counter()
                startup_times["Neo4j"] = (end_time - start_time) * 1000  # ms
                await driver.close()
            except Exception as e:
                if "Connection refused" not in str(e):
                    raise
                startup_times["Neo4j"] = None

        # Test FalkorDB startup time
        if not os.getenv("DISABLE_FALKORDB"):
            try:
                start_time = time.perf_counter()
                driver = get_driver(GraphProvider.FALKORDB)
                # Test connection
                await driver.execute_query("RETURN 1")
                end_time = time.perf_counter()
                startup_times["FalkorDB"] = (end_time - start_time) * 1000  # ms
                await driver.close()
            except Exception as e:
                if "Connection refused" not in str(
                    e
                ) and "No connection could be made" not in str(e):
                    raise
                startup_times["FalkorDB"] = None

        # Report results
        print(f"\nStartup Time Benchmark:")
        for db_name, startup_time in startup_times.items():
            if startup_time is not None:
                print(f"  {db_name}: {startup_time:.2f}ms")
            else:
                print(f"  {db_name}: Not available")

        # At least one database should be available
        available_times = [t for t in startup_times.values() if t is not None]
        assert (
            len(available_times) > 0
        ), "At least one database should be available for testing"
