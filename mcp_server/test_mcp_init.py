#!/usr/bin/env python3
"""
Test MCP server initialization directly.
"""

import os
import sys
import asyncio

sys.path.insert(0, ".")


async def test_mcp_init():
    # Set environment before importing
    os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
    os.environ["FALKORDB_URL"] = "redis://localhost:6379"
    os.environ["OPENAI_API_KEY"] = "dummy"

    print("=== Environment Variables ===")
    print(f"GRAPHITI_DB_TYPE: {os.getenv('GRAPHITI_DB_TYPE')}")
    print(f"FALKORDB_URL: {os.getenv('FALKORDB_URL')}")

    # Import after setting environment
    from graphiti_mcp_server import initialize_graphiti, graphiti_client, config

    print(f"\n=== Config Check ===")
    print(f"Config database type: {config.database.db_type}")

    try:
        print(f"\n=== Testing MCP Server Initialization ===")
        await initialize_graphiti()

        if graphiti_client:
            print(f"✅ Graphiti client initialized successfully!")
            print(f"Driver type: {type(graphiti_client.driver)}")
        else:
            print(f"❌ Graphiti client is None after initialization")

    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_init())
