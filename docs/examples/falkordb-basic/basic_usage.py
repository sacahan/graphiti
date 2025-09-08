#!/usr/bin/env python3
"""
Basic FalkorDB usage example with Graphiti.

This example demonstrates:
- FalkorDB connection setup
- Basic graph operations
- Performance monitoring
"""

import asyncio
import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure FalkorDB
os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
os.environ.setdefault("FALKORDB_URL", "redis://localhost:6379")
os.environ.setdefault("SEMAPHORE_LIMIT", "20")

from graphiti import Graphiti


async def main():
    """Demonstrate basic FalkorDB operations."""
    print("🚀 FalkorDB Basic Usage Example")
    print("=" * 50)

    # Track startup time
    start_time = time.time()

    # Initialize Graphiti with FalkorDB
    print("1. Initializing Graphiti with FalkorDB...")
    graphiti = Graphiti()

    startup_time = time.time() - start_time
    print(f"   ✅ Startup completed in {startup_time:.2f}s")

    if startup_time < 5.0:
        print("   🎉 Startup target achieved (<5s)")
    else:
        print("   ⚠️  Startup slower than target (5s)")

    # Check memory usage (if psutil available)
    try:
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"   📊 Memory usage: {memory_mb:.1f}MB")
        if memory_mb < 200:
            print("   🎉 Memory target achieved (<200MB)")
    except ImportError:
        print("   ℹ️  Install psutil for memory monitoring")

    print()

    # Add some test data
    print("2. Adding test episodes...")
    episodes = [
        {
            "name": "FalkorDB Setup",
            "content": "Successfully set up FalkorDB as graph database backend for improved performance.",
            "group_id": "setup",
        },
        {
            "name": "Performance Testing",
            "content": "FalkorDB demonstrates faster startup times and lower memory usage compared to Neo4j.",
            "group_id": "testing",
        },
        {
            "name": "Development Progress",
            "content": "Team adopted FalkorDB for all new projects due to container-friendly deployment.",
            "group_id": "development",
        },
    ]

    for i, episode in enumerate(episodes, 1):
        operation_start = time.time()

        await graphiti.add_episode(
            name=episode["name"],
            episode_body=episode["content"],
            group_id=episode["group_id"],
            reference_time=datetime.now(timezone.utc),
        )

        operation_time = time.time() - operation_start
        print(f"   Episode {i}: {episode['name']} ({operation_time:.3f}s)")

    print("   ✅ All episodes added successfully")
    print()

    # Search operations
    print("3. Testing search functionality...")

    search_queries = [
        ("FalkorDB performance", ["setup", "testing"]),
        ("development", ["development"]),
        ("startup memory", []),  # Search all groups
    ]

    for query, group_ids in search_queries:
        search_start = time.time()

        results = await graphiti.search(
            query=query, group_ids=group_ids if group_ids else None, num_results=5
        )

        search_time = time.time() - search_start
        print(f"   Query: '{query}' -> {len(results)} results ({search_time:.3f}s)")

        for result in results[:2]:  # Show first 2 results
            print(f"     - {result.name}: {result.content[:50]}...")

    print("   ✅ Search operations completed")
    print()

    # Performance summary
    print("4. Performance Summary")
    print("-" * 30)
    print(f"   Database Type: FalkorDB")
    print(f"   Startup Time: {startup_time:.2f}s {'✅' if startup_time < 5 else '⚠️'}")

    try:
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"   Memory Usage: {memory_mb:.1f}MB {'✅' if memory_mb < 200 else '⚠️'}")
    except:
        pass

    print(f"   Concurrency: {os.getenv('SEMAPHORE_LIMIT', '20')} operations")
    print()

    # Connection info
    print("5. Configuration Details")
    print("-" * 30)
    print(f"   GRAPHITI_DB_TYPE: {os.getenv('GRAPHITI_DB_TYPE')}")
    print(f"   FALKORDB_URL: {os.getenv('FALKORDB_URL')}")
    print(f"   SEMAPHORE_LIMIT: {os.getenv('SEMAPHORE_LIMIT')}")
    print(f"   MODEL_NAME: {os.getenv('MODEL_NAME', 'default')}")

    print()
    print("🎉 FalkorDB basic usage example completed successfully!")
    print("=" * 50)


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
        print("✅ FalkorDB connection verified")
    except Exception as e:
        print(f"❌ FalkorDB connection failed: {e}")
        print(
            "   Start FalkorDB with: docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest"
        )
        exit(1)

    # Run example
    asyncio.run(main())
