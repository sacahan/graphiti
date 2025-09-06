#!/usr/bin/env python3
"""
Test script to verify dual-database test infrastructure.

This script validates that:
1. Both Neo4j and FalkorDB drivers can be created
2. DriverFactory works correctly with environment variables
3. Basic database operations work on both backends
4. Test infrastructure is properly set up

Usage:
    python scripts/test_dual_database_setup.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.driver.factory import DriverFactory
from tests.helpers_test import get_driver


async def test_neo4j_driver():
    """Test Neo4j driver connectivity."""
    print("Testing Neo4j driver...")

    if os.getenv("DISABLE_NEO4J"):
        print("  Neo4j disabled - skipping")
        return False

    try:
        driver = get_driver(GraphProvider.NEO4J)
        result, _, _ = await driver.execute_query("RETURN 1 as test_value")
        assert result[0]["test_value"] == 1
        await driver.close()
        print("  ✓ Neo4j driver works correctly")
        return True
    except Exception as e:
        print(f"  ✗ Neo4j driver failed: {e}")
        return False


async def test_falkordb_driver():
    """Test FalkorDB driver connectivity."""
    print("Testing FalkorDB driver...")

    if os.getenv("DISABLE_FALKORDB"):
        print("  FalkorDB disabled - skipping")
        return False

    try:
        driver = get_driver(GraphProvider.FALKORDB)
        result, _, _ = await driver.execute_query("RETURN 1 as test_value")
        assert result[0]["test_value"] == 1
        await driver.close()
        print("  ✓ FalkorDB driver works correctly")
        return True
    except Exception as e:
        print(f"  ✗ FalkorDB driver failed: {e}")
        return False


async def test_driver_factory():
    """Test DriverFactory functionality."""
    print("Testing DriverFactory...")

    # Test with Neo4j
    if not os.getenv("DISABLE_NEO4J"):
        try:
            os.environ["GRAPHITI_DB_TYPE"] = "neo4j"
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "test")

            driver = DriverFactory.create_driver(
                uri=neo4j_uri, user=neo4j_user, password=neo4j_password
            )

            assert driver.provider == GraphProvider.NEO4J
            result, _, _ = await driver.execute_query("RETURN 1 as test_value")
            assert result[0]["test_value"] == 1
            await driver.close()
            print("  ✓ DriverFactory Neo4j creation works correctly")
        except Exception as e:
            print(f"  ✗ DriverFactory Neo4j creation failed: {e}")

    # Test with FalkorDB
    if not os.getenv("DISABLE_FALKORDB"):
        try:
            os.environ["GRAPHITI_DB_TYPE"] = "falkordb"

            driver = DriverFactory.create_driver()

            assert driver.provider == GraphProvider.FALKORDB
            result, _, _ = await driver.execute_query("RETURN 1 as test_value")
            assert result[0]["test_value"] == 1
            await driver.close()
            print("  ✓ DriverFactory FalkorDB creation works correctly")
        except Exception as e:
            print(f"  ✗ DriverFactory FalkorDB creation failed: {e}")

    # Clean up environment
    if "GRAPHITI_DB_TYPE" in os.environ:
        del os.environ["GRAPHITI_DB_TYPE"]


async def test_database_switching():
    """Test switching between databases."""
    print("Testing database switching...")

    if os.getenv("DISABLE_NEO4J") or os.getenv("DISABLE_FALKORDB"):
        print("  Both databases needed for switching test - skipping")
        return

    try:
        # Create Neo4j driver
        os.environ["GRAPHITI_DB_TYPE"] = "neo4j"
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "test")

        neo4j_driver = DriverFactory.create_driver(
            uri=neo4j_uri, user=neo4j_user, password=neo4j_password
        )

        # Create FalkorDB driver
        os.environ["GRAPHITI_DB_TYPE"] = "falkordb"
        falkor_driver = DriverFactory.create_driver()

        # Test both work
        result1, _, _ = await neo4j_driver.execute_query("RETURN 'neo4j' as db_type")
        result2, _, _ = await falkor_driver.execute_query(
            "RETURN 'falkordb' as db_type"
        )

        assert result1[0]["db_type"] == "neo4j"
        assert result2[0]["db_type"] == "falkordb"

        await neo4j_driver.close()
        await falkor_driver.close()

        print("  ✓ Database switching works correctly")

    except Exception as e:
        print(f"  ✗ Database switching failed: {e}")
    finally:
        # Clean up environment
        if "GRAPHITI_DB_TYPE" in os.environ:
            del os.environ["GRAPHITI_DB_TYPE"]


async def main():
    """Run all tests."""
    print("Validating dual-database test infrastructure...")
    print("=" * 50)

    neo4j_works = await test_neo4j_driver()
    falkor_works = await test_falkordb_driver()

    await test_driver_factory()
    await test_database_switching()

    print("=" * 50)

    if neo4j_works and falkor_works:
        print("✓ Both databases are available and working")
        print("✓ Dual-database test infrastructure is ready")
        return 0
    elif neo4j_works or falkor_works:
        print("⚠ Only one database is available - some tests will be skipped")
        print("✓ Single-database test infrastructure is ready")
        return 0
    else:
        print("✗ No databases are available")
        print("✗ Test infrastructure is not ready")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
