#!/usr/bin/env python3
"""
Simple test script to verify FalkorDB configuration.
"""

import os
import asyncio
import sys

sys.path.insert(0, ".")

from graphiti_mcp_server import DatabaseConfig, GraphitiConfig


def test_config():
    print("=== Environment Variables ===")
    print(f"GRAPHITI_DB_TYPE: {os.getenv('GRAPHITI_DB_TYPE')}")
    print(f"FALKORDB_URL: {os.getenv('FALKORDB_URL')}")
    print(f"OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")

    print("\n=== Database Config ===")
    db_config = DatabaseConfig.from_env()
    print(f"DB Type: {db_config.db_type}")
    print(f"URI: {db_config.uri}")
    print(f"Database: {db_config.database}")

    print("\n=== Full Graphiti Config ===")
    full_config = GraphitiConfig.from_env()
    print(f"DB Type: {full_config.database.db_type}")
    print(f"Group ID: {full_config.group_id}")
    print(f"Custom entities: {full_config.use_custom_entities}")


if __name__ == "__main__":
    test_config()
