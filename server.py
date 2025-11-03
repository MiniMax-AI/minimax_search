"""MiniMax Search MCP Server - Powerful web search and browsing tools"""

import asyncio
import json
import sys
import os
from typing import List
import logging

# Add project root directory to path
sys.path.append(os.path.dirname(__file__))

from minimax_search_browse import (
    get_searches_results,
    get_browses_results,
)

# MCP imports
try:
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
    )
except ImportError:
    print("Please install mcp package: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Configure logging - output to stderr to avoid polluting stdout (JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("minimax_search")


class MinimaxSearchMCPServer:
    """MiniMax Search MCP Server Implementation (Standard MCP Protocol)"""

    def __init__(self):
        self.app = Server("minimax_search")
        self._setup_tools()
        logger.info("MiniMax Search MCP Server initialized")

    def _setup_tools(self):
        """Setup MCP tools (Standard MCP Protocol)"""

        @self.app.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools (MCP Standard Protocol)"""
            return [
                Tool(
                    name="search",
                    description="Web search in parallel. The parameter is a list of queries. The queries will be sent to a search engine. You will get the brief search results with (title, url, snippet)s for each query.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "queries": {
                                "type": "array",
                                "description": "The queries. Google advanced search operators are supported.",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["queries"],
                    },
                ),
                Tool(
                    name="browse",
                    description="Explore specific information in a list of urls. The parameters are a url list and a query. The urls will be browsed, and each content will be sent to a Large Language Model (LLM) as the based information to answer the query.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "urls": {
                                "type": "array",
                                "description": "The url list.",
                                "items": {"type": "string"},
                            },
                            "query": {
                                "type": "string",
                                "description": "The query. A detailed natural language query is recommended.",
                            },
                        },
                        "required": ["urls", "query"],
                    },
                ),
            ]

        @self.app.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool calls (MCP Standard Protocol)"""
            logger.info(f"Calling tool: {name}, arguments: {arguments}")

            try:
                if name == "search":
                    result = get_searches_results(
                        queries=arguments["queries"],
                    )
                elif name == "browse":
                    result = get_browses_results(
                        urls=arguments["urls"], browse_query=arguments["query"]
                    )
                else:
                    result = json.dumps(
                        {
                            "success": False,
                            "error": f"Unknown tool: {name}",
                            "message": "Tool does not exist",
                        },
                        ensure_ascii=False,
                        indent=2,
                    )

                # Format output
                if isinstance(result, str):
                    output_text = result
                else:
                    output_text = json.dumps(result, ensure_ascii=False, indent=2)

                logger.info(f"Tool {name} executed successfully")
                return [TextContent(type="text", text=output_text)]

            except Exception as e:
                logger.error(f"Error handling tool call {name}: {e}", exc_info=True)
                error_result = {
                    "success": False,
                    "error": str(e),
                    "message": f"Error occurred while executing tool {name}",
                }
                error_text = json.dumps(error_result, ensure_ascii=False, indent=2)
                return [TextContent(type="text", text=error_text)]


async def async_main():
    """Async main function - Start MiniMax Search MCP Server"""
    logger.info("Starting MiniMax Search MCP Server...")

    try:
        server = MinimaxSearchMCPServer()

        # Run server via stdio (Standard MCP Protocol)
        async with stdio_server() as (read_stream, write_stream):
            await server.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="minimax_search",
                    server_version="1.0.0",
                    capabilities=server.app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        raise


def main():
    """Main entry function - For uvx startup (synchronous wrapper)"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("MiniMax Search server stopped")
    except Exception as e:
        logger.error(f"Server runtime error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
