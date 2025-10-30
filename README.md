# MiniMax Search MCP Server

[English Doc](./README.md) | [Chinese Doc](./README_zh.md)

MiniMax Search is an MCP (Model Context Protocol) server that provides web search and browsing capabilities.

## 🔧 Version Notes

This project uses the **standard MCP Server protocol**, compliant with MCP specifications:
- ✅ Complete `list_tools()` implementation
- ✅ Complete `call_tool()` implementation  
- ✅ Standard `stdio_server()` communication
- ✅ Fully consistent with tooltool implementation

## Features

- 🔍 **Multi-Engine Search**: Supports Google search engine
- 🚀 **Parallel Search**: Native support for parallel multi-query search
- 🌐 **Batch Browsing**: Support for batch browsing of multiple URLs
- 🤖 **Intelligent Understanding**: Uses MiniMax LLM to understand web content and answer questions
- 🎯 **Advanced Search**: Supports Google advanced search syntax
- 🔄 **Auto Fallback**: Automatically switches to other engines when search fails

## Quick Start

### Install via Git (Recommended)

```bash
# Run directly from Git repository
uvx --from git+ssh://git@github.com:MiniMax-AI/minimax_search.git minimax-search
```

### Install via Local Path (Development)

```bash
# Run from local directory
uvx --from /xxx/minimax_search minimax-search
```

### MCP Client Configuration

Add to your MCP client configuration file (e.g., `mcp.json`):

```json
{
  "mcpServers": {
    "minimax_search": {
      "command": "uvx",
      "args": [
        "--from",
        "git+ssh://git@github.com:MiniMax-AI/minimax_search.git",
        "minimax-search"
      ],
      "env": {
        "MINIMAX_API_KEY": "your_minimax_api_key",
        "SERPER_API_KEY": "your_serper_api_key",
        "JINA_API_KEY": "your_jina_api_key"
      }
    }
  }
}
```

## Available Tools

### 1. search - Parallel Web Search

Search multiple queries simultaneously, returning brief results (title, URL, snippet).

**Parameters**:
- `queries` (array of strings, required): List of queries, supports Google advanced search syntax

**Supported Search Engines**:
- Google Search (via Serper API)

**Advanced Search Syntax**:
- `site:example.com` - Limit to specific site
- `intitle:keyword` - Title contains keyword
- `inurl:keyword` - URL contains keyword
- `"exact match"` - Exact phrase match

**Example**:
```json
{
  "queries": ["Python asyncio tutorial", "Python threading vs asyncio"]
}
```

### 2. browse - Batch Intelligent Browsing

Visit multiple web pages, use MiniMax LLM to understand content and answer questions.

**Parameters**:
- `urls` (array of strings, required): List of target web page URLs
- `query` (string, required): Question to be answered

**Example**:
```json
{
  "urls": [
    "https://docs.python.org/3/library/asyncio.html",
    "https://realpython.com/async-io-python/"
  ],
  "query": "Summarize the main features and use cases of asyncio"
}
```

## Environment Variables Configuration

### Required Environment Variables

**Basic Search Functionality**:
- `SERPER_API_KEY`: Google Search
  - Get it from: https://serper.dev/
  - Free tier: 2,500 requests/month

**Web Browsing Functionality**:
- `JINA_API_KEY`: Web content reading
  - Get it from: https://jina.ai/
  - Free tier available

**Browse Functionality (LLM Understanding)**:
- `MINIMAX_API_KEY`: MiniMax API Key
  - Get it from: https://platform.minimax.io/

## Usage Examples

### Using in an Agent

Once the MCP server is started, the Agent can use the following tools:

**Parallel search for multiple queries**:
```
User: Search for "Python asyncio" and "Python threading" differences simultaneously

Agent: [Calls search tool]
→ search(queries=["Python asyncio", "Python threading"])
→ Returns search results for both queries (executed in parallel)
```

**Batch browse multiple web pages**:
```
User: Visit these links and summarize the main features of asyncio
     - https://docs.python.org/3/library/asyncio.html
     - https://realpython.com/async-io-python/

Agent: [Calls browse tool]
→ browse(
    urls=["https://docs.python.org/...", "https://realpython.com/..."],
    query="Summarize the main features of asyncio"
  )
→ Returns comprehensive summary and answer
```

## Technical Implementation

### Project Structure

```
minimax_search/
├── server.py                    # MCP Server entry point (2 tools)
├── minimax_search_browse.py     # Core search and browse implementation
├── pyproject.toml              # Project configuration
└── README.md
```

### Core Features

**Parallel Search**:
- Native support for queries array
- Concurrent execution using thread pool
- Automatic formatting and grouping of results

**Batch Browsing**:
- Native support for urls array
- Jina Reader extracts web content (converts to Markdown)
- MiniMax LLM understands content and generates comprehensive answers

## License

MIT

This project is based on the [MiniMax-M2 Model](https://github.com/MiniMax-AI/MiniMax-M2) project

