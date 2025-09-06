#!/usr/bin/env python3
"""
Comprehensive test script for FalkorDB performance testing.
"""

import asyncio
import os
import sys
import time
import psutil

sys.path.insert(0, ".")

from datetime import datetime, timezone
from graphiti_mcp_server import (
    GraphitiConfig,
    initialize_graphiti,
    graphiti_client,
    config,
)


async def test_falkor_performance():
    global config, graphiti_client

    print("🚀 Starting FalkorDB Performance Test")
    print("=" * 50)

    # Set configuration
    os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
    os.environ["FALKORDB_URL"] = "redis://localhost:6379"
    os.environ["OPENAI_API_KEY"] = "dummy"  # We'll disable custom entities

    # Reset global state
    graphiti_client = None
    config = GraphitiConfig.from_env()
    config.use_custom_entities = False  # Disable to avoid needing real API key

    # Measure memory
    process = psutil.Process()
    memory_start = process.memory_info().rss / 1024 / 1024

    # Test 1: Initialization
    print("📈 Test 1: Initialization Performance")
    start_time = time.time()

    try:
        await initialize_graphiti()
        init_time = time.time() - start_time
        memory_after_init = process.memory_info().rss / 1024 / 1024
        memory_used = memory_after_init - memory_start

        print(f"✅ Initialization: {init_time:.2f}s")
        print(
            f"📊 Memory usage: {memory_used:.1f}MB (current: {memory_after_init:.1f}MB)"
        )

        # Check performance targets
        startup_ok = init_time < 5.0
        memory_ok = memory_after_init < 200.0

        print(f"🎯 Startup < 5s: {'✅' if startup_ok else '❌'} ({init_time:.2f}s)")
        print(
            f"🎯 Memory < 200MB: {'✅' if memory_ok else '❌'} ({memory_after_init:.1f}MB)"
        )

        if graphiti_client:
            # Test 2: Connection
            print(f"\n📡 Test 2: Connection Performance")
            conn_start = time.time()
            # FalkorDB doesn't have verify_connectivity, so test with a simple query
            await graphiti_client.driver.execute_query("RETURN 1")
            conn_time = time.time() - conn_start
            print(f"✅ Connection verified: {conn_time:.3f}s")

            # Test 3: Basic Operation
            print(f"\n⚡ Test 3: Basic Operation Performance")
            op_start = time.time()
            await graphiti_client.add_episode(
                name="Performance Test Episode",
                episode_body="This is a test episode for FalkorDB performance verification.",
                group_id="perf_test_group",
                reference_time=datetime.now(timezone.utc),
                entity_types={},  # No custom entity extraction
            )
            op_time = time.time() - op_start
            print(f"✅ Episode added: {op_time:.3f}s")

            # Test 4: Search Operation
            print(f"\n🔍 Test 4: Search Performance")
            search_start = time.time()
            results = await graphiti_client.search(
                query="performance test", group_ids=["perf_test_group"], num_results=5
            )
            search_time = time.time() - search_start
            print(
                f"✅ Search completed: {search_time:.3f}s (found {len(results)} results)"
            )

        print(f"\n🎉 All tests completed successfully!")

        # Final performance summary
        print(f"\n📋 Performance Summary:")
        print(f"   Startup Time: {init_time:.2f}s {'✅' if startup_ok else '❌'}")
        print(
            f"   Memory Usage: {memory_after_init:.1f}MB {'✅' if memory_ok else '❌'}"
        )
        if startup_ok and memory_ok:
            print(f"   🏆 All performance targets achieved!")
        else:
            print(f"   ⚠️  Some performance targets missed")

    except Exception as e:
        init_time = time.time() - start_time
        print(f"❌ Test failed after {init_time:.2f}s: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_falkor_performance())
