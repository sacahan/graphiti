#!/usr/bin/env python3
"""
Test the DriverFactory directly to understand the issue.
"""

import os
import sys

sys.path.insert(0, "/Users/sacahan/Documents/workspace/graphiti")


def test_driver_factory():
    # Set environment
    os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
    os.environ["FALKORDB_URL"] = "redis://localhost:6379"

    print("=== Environment Variables ===")
    print(f"GRAPHITI_DB_TYPE: {os.getenv('GRAPHITI_DB_TYPE')}")
    print(f"FALKORDB_URL: {os.getenv('FALKORDB_URL')}")

    try:
        # Import and test DriverFactory directly
        from graphiti_core.driver.factory import DriverFactory

        print("\n=== Testing DriverFactory ===")
        driver = DriverFactory.create_driver(
            uri=None, user=None, password=None, database=None
        )
        print(f"Driver created successfully: {type(driver)}")

        # Test connection
        print("\n=== Testing Connection ===")
        import asyncio

        async def test_connection():
            await driver.client.verify_connectivity()
            print("Connection verified successfully!")

        asyncio.run(test_connection())

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_driver_factory()
