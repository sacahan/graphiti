#!/usr/bin/env python3
"""
Debug script to trace configuration issues.
"""

import os
import sys

sys.path.insert(0, ".")


def debug_config():
    # Set environment before importing
    os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
    os.environ["FALKORDB_URL"] = "redis://localhost:6379"
    os.environ["OPENAI_API_KEY"] = "dummy"

    print("=== Environment Variables ===")
    print(f"GRAPHITI_DB_TYPE: {os.getenv('GRAPHITI_DB_TYPE')}")
    print(f"FALKORDB_URL: {os.getenv('FALKORDB_URL')}")

    # Import after setting environment
    from graphiti_mcp_server import config, DatabaseConfig, GraphitiConfig

    print(f"\n=== Global Config at Import ===")
    print(f"Global config database type: {config.database.db_type}")

    print(f"\n=== Fresh Config from Env ===")
    fresh_config = GraphitiConfig.from_env()
    print(f"Fresh config database type: {fresh_config.database.db_type}")

    print(f"\n=== Updating Global Config ===")
    # Try to update the global config
    import graphiti_mcp_server

    graphiti_mcp_server.config = fresh_config

    print(
        f"Updated global config database type: {graphiti_mcp_server.config.database.db_type}"
    )

    return fresh_config


if __name__ == "__main__":
    fresh_config = debug_config()
