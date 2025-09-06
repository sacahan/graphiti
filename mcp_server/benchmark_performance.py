#!/usr/bin/env python3
"""
Performance benchmarking script for Graphiti MCP server with different database backends.

This script measures:
- Startup time for MCP server with Neo4j vs FalkorDB
- Memory usage during initialization and operation
- Database connection times
- Index building performance
- Basic operation performance (add_memory, search)

Usage:
    python benchmark_performance.py --database neo4j
    python benchmark_performance.py --database falkordb
    python benchmark_performance.py --compare  # Run both and compare
"""

import argparse
import asyncio
import os
import psutil
import time
import sys
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Import MCP server components
from graphiti_mcp_server import (
    GraphitiConfig,
    initialize_graphiti,
    graphiti_client,
    config as global_config,
)

load_dotenv()


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    database_type: str
    startup_time: float
    memory_usage_mb: float
    peak_memory_mb: float
    connection_time: float
    index_build_time: float
    first_operation_time: Optional[float] = None
    search_operation_time: Optional[float] = None
    error_message: Optional[str] = None


class PerformanceBenchmark:
    """Performance benchmarking for Graphiti MCP server."""

    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        return (
            self.process.memory_info().peak_wss / 1024 / 1024
            if hasattr(self.process.memory_info(), "peak_wss")
            else self.get_memory_usage()
        )

    async def benchmark_database(self, db_type: str) -> PerformanceMetrics:
        """Benchmark a specific database type."""
        global global_config, graphiti_client

        print(f"\n{'='*60}")
        print(f"Benchmarking {db_type.upper()}")
        print(f"{'='*60}")

        # Set environment for the database type
        os.environ["GRAPHITI_DB_TYPE"] = db_type

        if db_type == "falkordb":
            # Ensure FalkorDB-specific env vars are set with defaults
            os.environ.setdefault("FALKORDB_URL", "redis://localhost:6379")
            os.environ.setdefault("GRAPHITI_DB_NAME", "benchmark_db")
        elif db_type == "neo4j":
            # Ensure Neo4j-specific env vars are set
            if not os.environ.get("NEO4J_URI"):
                os.environ["NEO4J_URI"] = "bolt://localhost:7687"
            if not os.environ.get("NEO4J_USER"):
                os.environ["NEO4J_USER"] = "neo4j"
            if not os.environ.get("NEO4J_PASSWORD"):
                os.environ["NEO4J_PASSWORD"] = "password"

        metrics = PerformanceMetrics(
            database_type=db_type,
            startup_time=0,
            memory_usage_mb=0,
            peak_memory_mb=0,
            connection_time=0,
            index_build_time=0,
        )

        try:
            # Measure startup time
            startup_start = time.time()
            memory_start = self.get_memory_usage()

            print(f"Starting initialization...")

            # Reset global state
            graphiti_client = None

            # Recreate config for this database type
            global_config = GraphitiConfig.from_env()

            # Initialize Graphiti client
            await initialize_graphiti()

            startup_time = time.time() - startup_start
            memory_after_init = self.get_memory_usage()
            peak_memory = self.get_peak_memory()

            metrics.startup_time = startup_time
            metrics.memory_usage_mb = memory_after_init - memory_start
            metrics.peak_memory_mb = peak_memory

            print(f"✅ Initialization completed in {startup_time:.2f}s")
            print(
                f"📊 Memory usage: {metrics.memory_usage_mb:.1f}MB (peak: {peak_memory:.1f}MB)"
            )

            # Test basic connection
            if graphiti_client:
                conn_start = time.time()
                await graphiti_client.driver.client.verify_connectivity()
                metrics.connection_time = time.time() - conn_start
                print(f"🔗 Connection verified in {metrics.connection_time:.3f}s")

                # Measure a basic operation
                op_start = time.time()
                await graphiti_client.add_episode(
                    name="Benchmark Test",
                    episode_body="This is a test episode for benchmarking.",
                    group_id="benchmark_group",
                    reference_time=datetime.now(timezone.utc),
                )
                metrics.first_operation_time = time.time() - op_start
                print(
                    f"⚡ First add_episode operation: {metrics.first_operation_time:.3f}s"
                )

                # Measure search operation
                search_start = time.time()
                results = await graphiti_client.search(
                    query="benchmark test", group_ids=["benchmark_group"], num_results=5
                )
                metrics.search_operation_time = time.time() - search_start
                print(
                    f"🔍 Search operation: {metrics.search_operation_time:.3f}s (found {len(results)} results)"
                )

        except Exception as e:
            metrics.error_message = str(e)
            print(f"❌ Error during {db_type} benchmark: {e}")

        return metrics

    def print_comparison(
        self, neo4j_metrics: PerformanceMetrics, falkor_metrics: PerformanceMetrics
    ):
        """Print a comparison between Neo4j and FalkorDB performance."""
        print(f"\n{'='*80}")
        print("PERFORMANCE COMPARISON")
        print(f"{'='*80}")

        def format_comparison(
            label: str,
            neo4j_val: float,
            falkor_val: float,
            unit: str = "s",
            lower_is_better: bool = True,
        ):
            if neo4j_val == 0 or falkor_val == 0:
                return f"{label:<25} Neo4j: N/A, FalkorDB: N/A"

            if lower_is_better:
                improvement = ((neo4j_val - falkor_val) / neo4j_val) * 100
                winner = "FalkorDB" if falkor_val < neo4j_val else "Neo4j"
            else:
                improvement = ((falkor_val - neo4j_val) / neo4j_val) * 100
                winner = "FalkorDB" if falkor_val > neo4j_val else "Neo4j"

            status = "✅" if winner == "FalkorDB" else "⚠️"
            return f"{label:<25} Neo4j: {neo4j_val:.3f}{unit}, FalkorDB: {falkor_val:.3f}{unit} ({improvement:+.1f}%) {status}"

        print(
            format_comparison(
                "Startup Time", neo4j_metrics.startup_time, falkor_metrics.startup_time
            )
        )
        print(
            format_comparison(
                "Memory Usage",
                neo4j_metrics.memory_usage_mb,
                falkor_metrics.memory_usage_mb,
                "MB",
            )
        )
        print(
            format_comparison(
                "Peak Memory",
                neo4j_metrics.peak_memory_mb,
                falkor_metrics.peak_memory_mb,
                "MB",
            )
        )
        print(
            format_comparison(
                "Connection Time",
                neo4j_metrics.connection_time,
                falkor_metrics.connection_time,
            )
        )

        if neo4j_metrics.first_operation_time and falkor_metrics.first_operation_time:
            print(
                format_comparison(
                    "First Operation",
                    neo4j_metrics.first_operation_time,
                    falkor_metrics.first_operation_time,
                )
            )

        if neo4j_metrics.search_operation_time and falkor_metrics.search_operation_time:
            print(
                format_comparison(
                    "Search Operation",
                    neo4j_metrics.search_operation_time,
                    falkor_metrics.search_operation_time,
                )
            )

        # Check if FalkorDB meets targets
        print(f"\n{'='*50}")
        print("TARGET ACHIEVEMENT")
        print(f"{'='*50}")

        startup_target_met = falkor_metrics.startup_time < 5.0
        memory_target_met = falkor_metrics.peak_memory_mb < 200.0

        print(
            f"Startup Time < 5s:     {'✅ PASSED' if startup_target_met else '❌ FAILED'} ({falkor_metrics.startup_time:.2f}s)"
        )
        print(
            f"Peak Memory < 200MB:   {'✅ PASSED' if memory_target_met else '❌ FAILED'} ({falkor_metrics.peak_memory_mb:.1f}MB)"
        )

        if startup_target_met and memory_target_met:
            print("\n🎉 All performance targets achieved for FalkorDB!")
        else:
            print(
                "\n⚠️  Some performance targets not met. Consider further optimization."
            )


async def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Graphiti MCP server performance"
    )
    parser.add_argument(
        "--database", choices=["neo4j", "falkordb"], help="Database type to benchmark"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare both Neo4j and FalkorDB performance",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations to run (default: 1)",
    )

    args = parser.parse_args()

    # Configure logging to be less verbose during benchmarks
    logging.getLogger().setLevel(logging.WARNING)

    benchmark = PerformanceBenchmark()

    if args.compare:
        print("Running comparative benchmark between Neo4j and FalkorDB...")

        # Check if databases are available
        neo4j_available = os.environ.get("NEO4J_URI") and os.environ.get(
            "NEO4J_PASSWORD"
        )
        falkor_available = os.environ.get("FALKORDB_URL") or "redis://localhost:6379"

        if not neo4j_available:
            print(
                "⚠️  Neo4j configuration not found. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD"
            )
        if not falkor_available:
            print("⚠️  FalkorDB configuration not found. Set FALKORDB_URL")

        neo4j_metrics = (
            await benchmark.benchmark_database("neo4j") if neo4j_available else None
        )
        falkor_metrics = (
            await benchmark.benchmark_database("falkordb") if falkor_available else None
        )

        if neo4j_metrics and falkor_metrics:
            benchmark.print_comparison(neo4j_metrics, falkor_metrics)
        else:
            print("❌ Could not run comparison - missing database configuration")

    elif args.database:
        print(f"Running benchmark for {args.database}...")
        metrics = await benchmark.benchmark_database(args.database)

        if not metrics.error_message:
            print(f"\n✅ Benchmark completed successfully!")
        else:
            print(f"\n❌ Benchmark failed: {metrics.error_message}")
    else:
        print("Please specify --database or --compare")
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
