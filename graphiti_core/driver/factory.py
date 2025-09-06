"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
from typing import Optional

from graphiti_core.driver.driver import GraphDriver
from graphiti_core.driver.neo4j_driver import Neo4jDriver


class DriverFactory:
    """Factory class for creating database drivers based on configuration.

    The factory supports multiple database backends and determines which driver
    to instantiate based on environment variables or explicit configuration.
    """

    @staticmethod
    def create_driver(
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        config: Optional[dict] = None,
    ) -> GraphDriver:
        """
        Create a graph driver based on environment configuration.

        The driver type is determined by the GRAPHITI_DB_TYPE environment variable:
        - 'falkordb': Creates a FalkorDB driver with environment-based configuration
        - 'neo4j' (default): Creates a Neo4j driver with provided URI/credentials

        Args:
            uri: Database URI (required for Neo4j, ignored for FalkorDB)
            user: Username (required for Neo4j, ignored for FalkorDB)
            password: Password (required for Neo4j, may be used by FalkorDB)
            config: Optional configuration dictionary (currently unused, reserved for future extensions)

        Returns:
            GraphDriver: Configured driver instance

        Raises:
            ValueError: If required parameters are missing for the selected driver type
            ImportError: If the selected driver type is not available
        """
        db_type = os.getenv("GRAPHITI_DB_TYPE", "neo4j").lower()

        if db_type == "falkordb":
            try:
                from graphiti_core.driver.falkordb_driver import FalkorDriver

                return FalkorDriver()
            except ImportError as e:
                raise ImportError(
                    "FalkorDB driver is not available. "
                    "Install it with: pip install graphiti-core[falkordb]"
                ) from e
        elif db_type == "neo4j":
            if uri is None:
                raise ValueError("uri must be provided when using Neo4j driver")
            return Neo4jDriver(uri, user, password)
        else:
            raise ValueError(
                f"Unsupported database type: {db_type}. "
                "Supported types: 'neo4j', 'falkordb'"
            )
