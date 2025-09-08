#!/usr/bin/env python3
"""
Performance demonstration comparing Neo4j vs FalkorDB.

This example demonstrates:
- Side-by-side performance comparison
- Startup time measurements
- Memory usage analysis
- Concurrency benchmarks
"""

import asyncio
import os
import time
import statistics
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY environment variable is required")
    print("   Set with: export OPENAI_API_KEY=your-api-key")
    exit(1)

from graphiti import Graphiti


class PerformanceBenchmark:
    """Performance benchmark utility for database comparison."""

    def __init__(self, db_type: str):
        self.db_type = db_type
        self.startup_time = 0
        self.operation_times = []
        self.search_times = []
        self.memory_usage = 0

    async def run_benchmark(self, num_operations: int = 10):
        """Run comprehensive performance benchmark."""
        print(f"🔬 Running {self.db_type.upper()} Performance Benchmark")
        print("-" * 50)

        # Configure database
        os.environ["GRAPHITI_DB_TYPE"] = self.db_type

        if self.db_type == "falkordb":
            os.environ.setdefault("FALKORDB_URL", "redis://localhost:6379")
            os.environ.setdefault("SEMAPHORE_LIMIT", "20")
        elif self.db_type == "neo4j":
            os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
            os.environ.setdefault("NEO4J_USER", "neo4j")
            os.environ.setdefault("NEO4J_PASSWORD", "password")
            os.environ.setdefault("SEMAPHORE_LIMIT", "10")

        # Measure startup time
        print("1. Measuring startup performance...")
        startup_start = time.time()

        try:
            graphiti = Graphiti()
            self.startup_time = time.time() - startup_start
            print(f"   ✅ {self.db_type} initialized in {self.startup_time:.2f}s")
        except Exception as e:
            print(f"   ❌ {self.db_type} initialization failed: {e}")
            return False

        # Measure memory usage
        try:
            import psutil

            process = psutil.Process()
            self.memory_usage = process.memory_info().rss / 1024 / 1024
            print(f"   📊 Memory usage: {self.memory_usage:.1f}MB")
        except ImportError:
            print("   ℹ️  Install psutil for memory monitoring: pip install psutil")

        print()

        # Measure operation performance
        print(f"2. Testing {num_operations} add operations...")

        for i in range(num_operations):
            op_start = time.time()

            await graphiti.add_episode(
                name=f"Performance Test {i+1}",
                episode_body=f"Testing {self.db_type} performance with operation {i+1} of {num_operations}",
                group_id=f"perf-test-{self.db_type}",
                reference_time=datetime.now(timezone.utc),
            )

            op_time = time.time() - op_start
            self.operation_times.append(op_time)

            if (i + 1) % 5 == 0:
                avg_so_far = statistics.mean(self.operation_times)
                print(f"   Operations {i+1-4}-{i+1}: avg {avg_so_far:.3f}s")

        avg_op_time = statistics.mean(self.operation_times)
        print(f"   ✅ Average operation time: {avg_op_time:.3f}s")
        print()

        # Measure search performance
        print("3. Testing search performance...")

        search_queries = [
            f"performance test {self.db_type}",
            "testing operation",
            f"{self.db_type} benchmark",
            "performance",
            "test operation",
        ]

        for i, query in enumerate(search_queries):
            search_start = time.time()

            results = await graphiti.search(
                query=query, group_ids=[f"perf-test-{self.db_type}"], num_results=5
            )

            search_time = time.time() - search_start
            self.search_times.append(search_time)
            print(
                f"   Search {i+1}: '{query}' -> {len(results)} results ({search_time:.3f}s)"
            )

        avg_search_time = statistics.mean(self.search_times)
        print(f"   ✅ Average search time: {avg_search_time:.3f}s")
        print()

        return True

    def get_summary(self):
        """Get performance summary."""
        if not self.operation_times:
            return None

        return {
            "db_type": self.db_type,
            "startup_time": round(self.startup_time, 2),
            "memory_usage_mb": (
                round(self.memory_usage, 1) if self.memory_usage else None
            ),
            "avg_operation_time": round(statistics.mean(self.operation_times), 3),
            "min_operation_time": round(min(self.operation_times), 3),
            "max_operation_time": round(max(self.operation_times), 3),
            "avg_search_time": (
                round(statistics.mean(self.search_times), 3)
                if self.search_times
                else None
            ),
            "semaphore_limit": int(os.getenv("SEMAPHORE_LIMIT", "10")),
        }


def print_comparison(neo4j_summary, falkordb_summary):
    """Print side-by-side performance comparison."""
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 60)
    print()

    # Startup time comparison
    if neo4j_summary and falkordb_summary:
        neo4j_startup = neo4j_summary["startup_time"]
        falkor_startup = falkordb_summary["startup_time"]
        startup_improvement = ((neo4j_startup - falkor_startup) / neo4j_startup) * 100

        print(f"🚀 STARTUP TIME")
        print(f"   Neo4j:    {neo4j_startup}s")
        print(f"   FalkorDB: {falkor_startup}s")
        print(
            f"   Improvement: {startup_improvement:+.1f}% {'✅' if startup_improvement > 0 else '❌'}"
        )
        print()

    # Memory usage comparison
    if (
        neo4j_summary
        and falkordb_summary
        and neo4j_summary["memory_usage_mb"]
        and falkordb_summary["memory_usage_mb"]
    ):
        neo4j_memory = neo4j_summary["memory_usage_mb"]
        falkor_memory = falkordb_summary["memory_usage_mb"]
        memory_improvement = ((neo4j_memory - falkor_memory) / neo4j_memory) * 100

        print(f"💾 MEMORY USAGE")
        print(f"   Neo4j:    {neo4j_memory}MB")
        print(f"   FalkorDB: {falkor_memory}MB")
        print(
            f"   Improvement: {memory_improvement:+.1f}% {'✅' if memory_improvement > 0 else '❌'}"
        )
        print()

    # Operation speed comparison
    if neo4j_summary and falkordb_summary:
        neo4j_ops = neo4j_summary["avg_operation_time"]
        falkor_ops = falkordb_summary["avg_operation_time"]
        ops_improvement = ((neo4j_ops - falkor_ops) / neo4j_ops) * 100

        print(f"⚡ OPERATION SPEED")
        print(f"   Neo4j:    {neo4j_ops}s avg")
        print(f"   FalkorDB: {falkor_ops}s avg")
        print(
            f"   Improvement: {ops_improvement:+.1f}% {'✅' if ops_improvement > 0 else '❌'}"
        )
        print()

    # Search speed comparison
    if (
        neo4j_summary
        and falkordb_summary
        and neo4j_summary["avg_search_time"]
        and falkordb_summary["avg_search_time"]
    ):
        neo4j_search = neo4j_summary["avg_search_time"]
        falkor_search = falkordb_summary["avg_search_time"]
        search_improvement = ((neo4j_search - falkor_search) / neo4j_search) * 100

        print(f"🔍 SEARCH SPEED")
        print(f"   Neo4j:    {neo4j_search}s avg")
        print(f"   FalkorDB: {falkor_search}s avg")
        print(
            f"   Improvement: {search_improvement:+.1f}% {'✅' if search_improvement > 0 else '❌'}"
        )
        print()

    # Concurrency comparison
    if neo4j_summary and falkordb_summary:
        neo4j_concurrency = neo4j_summary["semaphore_limit"]
        falkor_concurrency = falkordb_summary["semaphore_limit"]
        concurrency_improvement = (
            (falkor_concurrency - neo4j_concurrency) / neo4j_concurrency
        ) * 100

        print(f"🔄 CONCURRENCY")
        print(f"   Neo4j:    {neo4j_concurrency} operations")
        print(f"   FalkorDB: {falkor_concurrency} operations")
        print(
            f"   Improvement: {concurrency_improvement:+.1f}% {'✅' if concurrency_improvement > 0 else '❌'}"
        )
        print()


async def main():
    """Run performance comparison demo."""
    print("🏁 FalkorDB vs Neo4j Performance Demo")
    print("=" * 60)
    print()

    # Check database availability
    databases_available = []

    # Check FalkorDB
    try:
        import redis

        r = redis.from_url("redis://localhost:6379")
        r.ping()
        databases_available.append("falkordb")
        print("✅ FalkorDB available at localhost:6379")
    except Exception as e:
        print(f"⚠️  FalkorDB not available: {e}")
        print(
            "   Start with: docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest"
        )

    # Check Neo4j (optional for comparison)
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        driver.verify_connectivity()
        driver.close()
        databases_available.append("neo4j")
        print("✅ Neo4j available at localhost:7687")
    except Exception as e:
        print(f"⚠️  Neo4j not available (optional for comparison): {e}")

    print()

    if "falkordb" not in databases_available:
        print("❌ FalkorDB is required for this demo")
        return

    # Run benchmarks
    neo4j_summary = None
    falkordb_summary = None

    # Benchmark FalkorDB (always run)
    falkor_benchmark = PerformanceBenchmark("falkordb")
    if await falkor_benchmark.run_benchmark():
        falkordb_summary = falkor_benchmark.get_summary()

    # Benchmark Neo4j (if available)
    if "neo4j" in databases_available:
        print()
        neo4j_benchmark = PerformanceBenchmark("neo4j")
        if await neo4j_benchmark.run_benchmark():
            neo4j_summary = neo4j_benchmark.get_summary()

    print()

    # Print comparison
    if falkordb_summary:
        if neo4j_summary:
            print_comparison(neo4j_summary, falkordb_summary)
        else:
            print("📊 FALKORDB PERFORMANCE RESULTS")
            print("=" * 40)
            print(f"🚀 Startup Time: {falkordb_summary['startup_time']}s")
            if falkordb_summary["memory_usage_mb"]:
                print(f"💾 Memory Usage: {falkordb_summary['memory_usage_mb']}MB")
            print(f"⚡ Avg Operation: {falkordb_summary['avg_operation_time']}s")
            if falkordb_summary["avg_search_time"]:
                print(f"🔍 Avg Search: {falkordb_summary['avg_search_time']}s")
            print(f"🔄 Concurrency: {falkordb_summary['semaphore_limit']} operations")
            print()

    # Performance targets achieved?
    print("🎯 PERFORMANCE TARGETS")
    print("=" * 30)

    if falkordb_summary:
        startup_target = falkordb_summary["startup_time"] < 5.0
        memory_target = (falkordb_summary["memory_usage_mb"] or 0) < 200
        operation_target = falkordb_summary["avg_operation_time"] < 1.0

        print(
            f"✅ Startup < 5s: {startup_target} ({falkordb_summary['startup_time']}s)"
        )
        if falkordb_summary["memory_usage_mb"]:
            print(
                f"✅ Memory < 200MB: {memory_target} ({falkordb_summary['memory_usage_mb']}MB)"
            )
        print(
            f"✅ Operations < 1s: {operation_target} ({falkordb_summary['avg_operation_time']}s)"
        )

        all_targets = (
            startup_target
            and (memory_target or not falkordb_summary["memory_usage_mb"])
            and operation_target
        )

        print()
        if all_targets:
            print("🎉 ALL PERFORMANCE TARGETS ACHIEVED!")
        else:
            print("⚠️  Some performance targets not met - consider tuning")

    print()
    print("Demo completed! 🏁")


if __name__ == "__main__":
    asyncio.run(main())
