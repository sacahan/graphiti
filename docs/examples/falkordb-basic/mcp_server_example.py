#!/usr/bin/env python3
"""
MCP Server example with FalkorDB backend.

This example demonstrates:
- MCP server configuration with FalkorDB
- Performance monitoring integration
- Container deployment setup
"""

import asyncio
import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure FalkorDB for MCP server
os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
os.environ.setdefault("FALKORDB_URL", "redis://localhost:6379")
os.environ.setdefault("SEMAPHORE_LIMIT", "20")
os.environ.setdefault("MCP_SERVER_HOST", "localhost")
os.environ.setdefault("MCP_SERVER_PORT", "8000")

from graphiti import Graphiti


async def main():
    """Demonstrate MCP server setup with FalkorDB."""
    print("🔧 MCP Server with FalkorDB Example")
    print("=" * 50)

    # Track initialization time
    start_time = time.time()

    # Initialize Graphiti (same as MCP server would do)
    print("1. Initializing Graphiti for MCP server...")
    graphiti = Graphiti()

    init_time = time.time() - start_time
    print(f"   ✅ MCP server ready in {init_time:.2f}s")

    if init_time < 5.0:
        print("   🎉 MCP startup target achieved (<5s)")
    else:
        print("   ⚠️  MCP startup slower than target (5s)")

    # Memory monitoring (simulating MCP server performance endpoint)
    try:
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"   📊 MCP server memory usage: {memory_mb:.1f}MB")

        if memory_mb < 200:
            print("   🎉 Memory target achieved (<200MB)")
        else:
            print("   ⚠️  Memory usage above target (200MB)")
    except ImportError:
        print("   ℹ️  Install psutil for memory monitoring: pip install psutil")

    print()

    # Simulate MCP server operations
    print("2. Simulating MCP server operations...")

    # Add memory (similar to MCP server add_memory tool)
    memories = [
        {
            "name": "MCP Server Setup",
            "content": "Successfully configured MCP server with FalkorDB backend for improved performance.",
            "group_id": "mcp-setup",
        },
        {
            "name": "Performance Monitoring",
            "content": "MCP server includes real-time performance monitoring with startup and memory metrics.",
            "group_id": "mcp-monitoring",
        },
        {
            "name": "Container Deployment",
            "content": "MCP server deployed using Docker with optimized FalkorDB container for fast startup.",
            "group_id": "mcp-deployment",
        },
    ]

    operation_times = []

    for i, memory in enumerate(memories, 1):
        op_start = time.time()

        await graphiti.add_episode(
            name=memory["name"],
            episode_body=memory["content"],
            group_id=memory["group_id"],
            reference_time=datetime.now(timezone.utc),
        )

        op_time = time.time() - op_start
        operation_times.append(op_time)
        print(f"   Memory {i}: {memory['name']} ({op_time:.3f}s)")

    avg_op_time = sum(operation_times) / len(operation_times)
    print(f"   ✅ Average operation time: {avg_op_time:.3f}s")
    print()

    # Simulate search operations (similar to MCP server search_memory tool)
    print("3. Testing MCP search functionality...")

    search_queries = [
        ("MCP server performance", ["mcp-setup", "mcp-monitoring"]),
        ("container deployment", ["mcp-deployment"]),
        ("FalkorDB", []),  # Search all groups
    ]

    search_times = []

    for query, group_ids in search_queries:
        search_start = time.time()

        results = await graphiti.search(
            query=query, group_ids=group_ids if group_ids else None, num_results=5
        )

        search_time = time.time() - search_start
        search_times.append(search_time)
        print(f"   Query: '{query}' -> {len(results)} results ({search_time:.3f}s)")

        # Show first result
        if results:
            print(f"     - {results[0].name}: {results[0].content[:60]}...")

    avg_search_time = sum(search_times) / len(search_times)
    print(f"   ✅ Average search time: {avg_search_time:.3f}s")
    print()

    # MCP Server Configuration Summary
    print("4. MCP Server Configuration")
    print("-" * 30)
    print(f"   Database Backend: FalkorDB")
    print(f"   Server Host: {os.getenv('MCP_SERVER_HOST', 'localhost')}")
    print(f"   Server Port: {os.getenv('MCP_SERVER_PORT', '8000')}")
    print(f"   Concurrency Limit: {os.getenv('SEMAPHORE_LIMIT', '20')}")
    print(f"   Startup Time: {init_time:.2f}s {'✅' if init_time < 5 else '⚠️'}")

    try:
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"   Memory Usage: {memory_mb:.1f}MB {'✅' if memory_mb < 200 else '⚠️'}")
    except:
        pass

    print()

    # MCP Tools Simulation
    print("5. MCP Tools Available")
    print("-" * 30)
    print("   📝 add_memory - Store information in graph")
    print("   🔍 search_memory - Semantic + keyword search")
    print("   📊 get_performance - Server performance metrics")
    print("   ❤️  health_check - Server health status")
    print()

    # Simulate performance endpoint response
    print("6. Performance Endpoint Response")
    print("-" * 30)
    performance_data = {
        "startup_time_seconds": round(init_time, 2),
        "average_operation_time_seconds": round(avg_op_time, 3),
        "average_search_time_seconds": round(avg_search_time, 3),
        "database_type": "falkordb",
        "semaphore_limit": int(os.getenv("SEMAPHORE_LIMIT", "20")),
        "status": "healthy" if init_time < 5 and avg_op_time < 1 else "degraded",
    }

    try:
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        performance_data["memory_usage_mb"] = round(memory_mb, 1)
    except:
        pass

    import json

    print(f"   {json.dumps(performance_data, indent=6)}")
    print()

    print("🎉 MCP Server example completed successfully!")
    print("=" * 50)
    print()
    print("Next Steps:")
    print("- Start actual MCP server: cd mcp_server && python graphiti_mcp_server.py")
    print("- Test endpoints: curl http://localhost:8000/status")
    print("- Monitor performance: curl http://localhost:8000/performance")


if __name__ == "__main__":
    # Check required environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("   Set with: export OPENAI_API_KEY=your-api-key")
        exit(1)

    # Check FalkorDB connection
    try:
        import redis

        r = redis.from_url(os.getenv("FALKORDB_URL", "redis://localhost:6379"))
        r.ping()
        print("✅ FalkorDB connection verified for MCP server")
    except Exception as e:
        print(f"❌ FalkorDB connection failed: {e}")
        print(
            "   Start FalkorDB with: docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest"
        )
        exit(1)

    # Run MCP server example
    asyncio.run(main())
