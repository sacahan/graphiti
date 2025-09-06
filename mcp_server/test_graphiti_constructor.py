#!/usr/bin/env python3
"""
Test the Graphiti constructor directly to understand the issue.
"""

import os
import sys

sys.path.insert(0, "/Users/sacahan/Documents/workspace/graphiti")


def test_graphiti_constructor():
    # Set environment
    os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
    os.environ["FALKORDB_URL"] = "redis://localhost:6379"
    os.environ["OPENAI_API_KEY"] = "dummy"

    print("=== Environment Variables ===")
    print(f"GRAPHITI_DB_TYPE: {os.getenv('GRAPHITI_DB_TYPE')}")
    print(f"FALKORDB_URL: {os.getenv('FALKORDB_URL')}")

    try:
        # Import and test Graphiti constructor directly
        from graphiti_core.graphiti import Graphiti

        print("\n=== Testing Graphiti Constructor ===")
        print("Attempting to create Graphiti instance with uri=None...")

        client = Graphiti(
            uri=None,
            user=None,
            password=None,
            database=None,
            llm_client=None,  # Allow defaults
            embedder=None,  # Allow defaults
        )
        print(f"Graphiti instance created successfully!")
        print(f"Driver type: {type(client.driver)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_graphiti_constructor()
