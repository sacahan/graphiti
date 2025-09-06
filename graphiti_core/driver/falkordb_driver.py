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

import logging
import os
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from falkordb import Graph as FalkorGraph
    from falkordb.asyncio import FalkorDB
else:
    try:
        from falkordb import Graph as FalkorGraph
        from falkordb.asyncio import FalkorDB
    except ImportError:
        # If falkordb is not installed, raise an ImportError
        raise ImportError(
            "falkordb is required for FalkorDriver. "
            "Install it with: pip install graphiti-core[falkordb]"
        ) from None

from graphiti_core.driver.driver import GraphDriver, GraphDriverSession, GraphProvider
from graphiti_core.utils.datetime_utils import convert_datetimes_to_strings

logger = logging.getLogger(__name__)


class FalkorDBConfig(BaseModel):
    """Configuration for FalkorDB database connection.

    This configuration supports both individual environment variables and
    Redis-style connection string format as alternatives.

    Environment Variables:
    - FALKORDB_HOST: FalkorDB server host (default: localhost)
    - FALKORDB_PORT: FalkorDB server port (default: 6379)
    - FALKORDB_DATABASE: Database number (default: 0)
    - FALKORDB_PASSWORD: Authentication password (optional)
    - FALKORDB_CONNECTION_STRING: Alternative Redis-style connection string

    Connection String Format:
    redis://[:password@]host:port/db
    """

    host: str = Field(default="localhost", description="FalkorDB server host")
    port: int = Field(default=6379, description="FalkorDB server port")
    database: int = Field(default=0, description="Database number")
    password: str | None = Field(default=None, description="Authentication password")
    connection_string: str | None = Field(
        default=None, description="Redis-style connection string"
    )

    @classmethod
    def from_env(cls) -> "FalkorDBConfig":
        """Create FalkorDBConfig from environment variables.

        Supports both individual variables and connection string format.
        Connection string takes precedence if provided.

        Returns:
            FalkorDBConfig: Configured instance
        """
        connection_string = os.getenv("FALKORDB_CONNECTION_STRING")

        if connection_string:
            return cls.from_connection_string(connection_string)

        # Use individual environment variables with defaults
        return cls(
            host=os.getenv("FALKORDB_HOST", "localhost"),
            port=int(os.getenv("FALKORDB_PORT", "6379")),
            database=int(os.getenv("FALKORDB_DATABASE", "0")),
            password=os.getenv("FALKORDB_PASSWORD"),
        )

    @classmethod
    def from_connection_string(cls, connection_string: str) -> "FalkorDBConfig":
        """Create FalkorDBConfig from Redis-style connection string.

        Args:
            connection_string: Redis-style connection string
                Format: redis://[:password@]host:port/db
                Examples:
                - redis://localhost:6379/0
                - redis://:password@localhost:6379/0
                - redis://user:password@host:6379/1

        Returns:
            FalkorDBConfig: Configured instance

        Raises:
            ValueError: If connection string format is invalid
        """
        if not connection_string:
            raise ValueError("Connection string cannot be empty")

        # Parse the connection string
        parsed = urlparse(connection_string)

        if parsed.scheme != "redis":
            raise ValueError(
                f"Invalid connection string scheme: {parsed.scheme}. Expected: redis"
            )

        host = parsed.hostname or "localhost"
        port = parsed.port or 6379

        # Extract database number from path
        database = 0
        if parsed.path and len(parsed.path) > 1:  # Skip leading '/'
            db_str = parsed.path[1:]  # Remove leading '/'
            try:
                database = int(db_str)
            except ValueError as e:
                raise ValueError(
                    f"Invalid database number in connection string: {db_str}"
                ) from e

        # Extract password
        password = parsed.password

        return cls(
            host=host,
            port=port,
            database=database,
            password=password,
            connection_string=connection_string,
        )

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is within valid range."""
        if not (1 <= v <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got: {v}")
        return v

    @field_validator("database")
    @classmethod
    def validate_database(cls, v: int) -> int:
        """Validate database number is non-negative."""
        if v < 0:
            raise ValueError(f"Database number must be non-negative, got: {v}")
        return v

    @field_validator("connection_string")
    @classmethod
    def validate_connection_string(cls, v: str | None) -> str | None:
        """Validate connection string format if provided."""
        if v is None:
            return v

        if not v.strip():
            raise ValueError("Connection string cannot be empty")

        # Basic check for redis scheme
        if not v.startswith("redis://"):
            raise ValueError(
                f"Invalid connection string format: {v}. "
                "Expected format: redis://[user][:password]@[host][:port][/db]"
            )

        # Check for empty redis://
        if v == "redis://":
            raise ValueError(
                f"Invalid connection string format: {v}. "
                "Expected format: redis://[user][:password]@[host][:port][/db]"
            )

        # Validate Redis-style connection string format with more lenient pattern
        # Allow:
        # redis://host
        # redis://host:port
        # redis://host:port/db
        # redis://:password@host:port/db
        # redis://user:password@host:port/db
        # redis://:password@:port/db (empty host, use for localhost)
        redis_url_pattern = re.compile(
            r"^redis://(?:(?:([^:/@]*):?([^@/]*)@)?([^:/@]+|:(?:\d+)?)?(?::(\d+))?)?(?:/(\d+))?$"
        )

        if not redis_url_pattern.match(v):
            raise ValueError(
                f"Invalid connection string format: {v}. "
                "Expected format: redis://[user][:password]@[host][:port][/db]"
            )

        return v

    def get_client_kwargs(self) -> dict[str, Any]:
        """Get keyword arguments for FalkorDB client initialization.

        Returns:
            dict: Keyword arguments for FalkorDB constructor
        """
        kwargs = {
            "host": self.host,
            "port": self.port,
        }

        if self.password:
            kwargs["password"] = self.password

        return kwargs

    def get_database_name(self) -> str:
        """Get database name for graph selection.

        For FalkorDB, the database number needs to be converted to a string
        for use with select_graph().

        Returns:
            str: Database identifier as string
        """
        if self.database == 0:
            return "default_db"  # FalkorDB default database name
        return str(self.database)


class FalkorDriverSession(GraphDriverSession):
    provider = GraphProvider.FALKORDB

    def __init__(self, graph: FalkorGraph):
        self.graph = graph

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # No cleanup needed for Falkor, but method must exist
        pass

    async def close(self):
        # No explicit close needed for FalkorDB, but method must exist
        pass

    async def execute_write(self, func, *args, **kwargs):
        # Directly await the provided async function with `self` as the transaction/session
        return await func(self, *args, **kwargs)

    async def run(self, query: str | list, **kwargs: Any) -> Any:
        # FalkorDB does not support argument for Label Set, so it's converted into an array of queries
        if isinstance(query, list):
            for cypher, params in query:
                params = convert_datetimes_to_strings(params)
                await self.graph.query(str(cypher), params)  # type: ignore[reportUnknownArgumentType]
        else:
            params = dict(kwargs)
            params = convert_datetimes_to_strings(params)
            await self.graph.query(str(query), params)  # type: ignore[reportUnknownArgumentType]
        # Assuming `graph.query` is async (ideal); otherwise, wrap in executor
        return None


class FalkorDriver(GraphDriver):
    provider = GraphProvider.FALKORDB

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        falkor_db: FalkorDB | None = None,
        database: str | None = None,
        config: FalkorDBConfig | None = None,
    ):
        """
        Initialize the FalkorDB driver.

        FalkorDB is a multi-tenant graph database.
        To connect, provide the host and port or use environment variables.

        Parameters can be provided in multiple ways (in order of precedence):
        1. Direct parameters (host, port, username, password, database)
        2. FalkorDBConfig instance
        3. Environment variables (FALKORDB_*)
        4. Default values

        Args:
            host: FalkorDB server host (overrides config and environment)
            port: FalkorDB server port (overrides config and environment)
            username: Username for authentication (legacy parameter, use password)
            password: Password for authentication (overrides config and environment)
            falkor_db: Pre-configured FalkorDB instance to use directly
            database: Database name/number (overrides config and environment)
            config: FalkorDBConfig instance with connection parameters
        """
        super().__init__()

        if falkor_db is not None:
            # If a FalkorDB instance is provided, use it directly
            self.client = falkor_db
            # Use provided database or default
            self._database = database or "default_db"
        else:
            # Determine configuration in order of precedence
            if config is None:
                # Load from environment if no config provided
                try:
                    config = FalkorDBConfig.from_env()
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Failed to load FalkorDB configuration from environment: {e}"
                    ) from e

            # Override config values with any direct parameters provided
            connection_params = config.get_client_kwargs()

            if host is not None:
                connection_params["host"] = host
            if port is not None:
                connection_params["port"] = port
            if password is not None:
                connection_params["password"] = password
            if username is not None and "password" not in connection_params:
                # Support legacy username parameter by setting it as password if password not provided
                connection_params["password"] = username

            # Initialize the FalkorDB client
            self.client = FalkorDB(**connection_params)

            # Set database name
            if database is not None:
                self._database = database
            else:
                self._database = config.get_database_name()

        self.fulltext_syntax = "@"  # FalkorDB uses a redisearch-like syntax for fulltext queries see https://redis.io/docs/latest/develop/ai/search-and-query/query/full-text/

    def _get_graph(self, graph_name: str | None) -> FalkorGraph:
        # FalkorDB requires a non-None database name for multi-tenant graphs; the default is "default_db"
        if graph_name is None:
            graph_name = self._database
        return self.client.select_graph(graph_name)

    async def execute_query(self, cypher_query_, **kwargs: Any):
        graph = self._get_graph(self._database)

        # Convert datetime objects to ISO strings (FalkorDB does not support datetime objects directly)
        params = convert_datetimes_to_strings(dict(kwargs))

        try:
            result = await graph.query(cypher_query_, params)  # type: ignore[reportUnknownArgumentType]
        except Exception as e:
            if "already indexed" in str(e):
                # check if index already exists
                logger.info(f"Index already exists: {e}")
                return None
            logger.error(
                f"Error executing FalkorDB query: {e}\n{cypher_query_}\n{params}"
            )
            raise

        # Convert the result header to a list of strings
        header = [h[1] for h in result.header]

        # Convert FalkorDB's result format (list of lists) to the format expected by Graphiti (list of dicts)
        records = []
        for row in result.result_set:
            record = {}
            for i, field_name in enumerate(header):
                if i < len(row):
                    record[field_name] = row[i]
                else:
                    # If there are more fields in header than values in row, set to None
                    record[field_name] = None
            records.append(record)

        return records, header, None

    def session(self, database: str | None = None) -> GraphDriverSession:
        return FalkorDriverSession(self._get_graph(database))

    async def close(self) -> None:
        """Close the driver connection."""
        if hasattr(self.client, "aclose"):
            await self.client.aclose()  # type: ignore[reportUnknownMemberType]
        elif hasattr(self.client.connection, "aclose"):
            await self.client.connection.aclose()
        elif hasattr(self.client.connection, "close"):
            await self.client.connection.close()

    async def delete_all_indexes(self) -> None:
        await self.execute_query(
            "CALL db.indexes() YIELD name DROP INDEX name",
        )

    def clone(self, database: str) -> "GraphDriver":
        """
        Returns a shallow copy of this driver with a different default database.
        Reuses the same connection (e.g. FalkorDB, Neo4j).
        """
        cloned = FalkorDriver(falkor_db=self.client, database=database)

        return cloned
