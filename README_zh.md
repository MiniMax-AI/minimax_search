# MiniMax Search MCP Server

[英文文档](./README.md) | [中文文档](./README_zh.md)

MiniMax Search 是一个MCP (Model Context Protocol) 服务器，提供网页搜索和浏览功能。

## 🔧 版本说明

本项目使用**标准 MCP Server 协议**，符合 MCP 规范：
- ✅ 完整的 `list_tools()` 实现
- ✅ 完整的 `call_tool()` 实现  
- ✅ 标准 `stdio_server()` 通信
- ✅ 与 tooltool 实现方式完全一致

## 特性

- 🔍 **多引擎搜索**: 支持 Google 搜索引擎
- 🚀 **并行搜索**: 原生支持多查询并行搜索
- 🌐 **批量浏览**: 支持批量浏览多个 URL
- 🤖 **智能理解**: 使用 MiniMax LLM 理解网页内容并回答问题
- 🎯 **高级搜索**: 支持 Google 高级搜索语法
- 🔄 **自动切换**: 搜索失败时自动切换到其他引擎

## 快速开始

### 通过 Git 安装（推荐）

```bash
# 从 Git 仓库直接运行
uvx --from git+ssh://git@github.com:MiniMax-AI/minimax_search.git minimax-search
```

### 通过本地路径安装（开发）

```bash
# 从本地目录运行
uvx --from /xxx/minimax_search minimax-search
```

### MCP 客户端配置

在你的 MCP 客户端配置文件 (例如 `mcp.json`) 中添加：

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

## 可用工具

### 1. search - 并行网页搜索

同时搜索多个查询，返回简要结果（标题、URL、摘要）。

**参数**:
- `queries` (array of strings, required): 查询列表，支持 Google 高级搜索语法

**支持的搜索引擎**:
- Google 搜索（通过 Serper API）

**高级搜索语法**:
- `site:example.com` - 限定站点
- `intitle:关键词` - 标题包含
- `inurl:关键词` - URL包含
- `"精确匹配"` - 精确短语匹配

**示例**:
```json
{
  "queries": ["Python asyncio tutorial", "Python threading vs asyncio"]
}
```

### 2. browse - 批量智能浏览

访问多个网页，使用 MiniMax LLM 理解内容并回答问题。

**参数**:
- `urls` (array of strings, required): 目标网页 URL 列表
- `query` (string, required): 要回答的问题

**示例**:
```json
{
  "urls": [
    "https://docs.python.org/3/library/asyncio.html",
    "https://realpython.com/async-io-python/"
  ],
  "query": "总结 asyncio 的主要特性和使用场景"
}
```

## 环境变量配置

### 必需的环境变量

**基础搜索功能**:
- `SERPER_API_KEY`: Google 搜索
  - 获取: https://serper.dev/
  - 免费额度: 2,500 次/月

**网页浏览功能**:
- `JINA_API_KEY`: 网页内容读取
  - 获取: https://jina.ai/
  - 有免费额度

**Browse 功能（LLM 理解）**:
- `MINIMAX_API_KEY`: MiniMax API Key
  - 获取: https://platform.minimaxi.com

## 使用示例

### 在 Agent 中使用

当 MCP 服务器启动后，Agent 可以使用以下工具：

**并行搜索多个查询**:
```
用户: 同时搜索 "Python asyncio" 和 "Python threading" 的区别

Agent: [调用 search 工具]
→ search(queries=["Python asyncio", "Python threading"])
→ 返回两个查询的搜索结果（并行执行）
```

**批量浏览多个网页**:
```
用户: 访问这些链接并总结 asyncio 的主要特性
     - https://docs.python.org/3/library/asyncio.html
     - https://realpython.com/async-io-python/

Agent: [调用 browse 工具]
→ browse(
    urls=["https://docs.python.org/...", "https://realpython.com/..."],
    query="总结 asyncio 的主要特性"
  )
→ 返回综合摘要和回答
```

## 技术实现

### 项目结构

```
minimax_search/
├── server.py                    # MCP Server 入口（2个工具）
├── minimax_search_browse.py     # 搜索和浏览核心实现
├── pyproject.toml              # 项目配置
└── README.md
```

### 核心特性

**并行搜索**:
- 原生支持 queries 数组
- 使用线程池并发执行
- 自动格式化和分组结果

**批量浏览**:
- 原生支持 urls 数组
- Jina Reader 提取网页内容（转 Markdown）
- MiniMax LLM 理解内容并生成综合回答

## 许可

MIT

本项目基于 [MiniMax-M2模型](https://github.com/MiniMax-AI/MiniMax-M2) 项目

