# meGPT Author Content MCP Server

This directory contains a Model Context Protocol (MCP) server that serves any meGPT author's content collection to AI applications. The server provides tools, resources, and prompts for AI systems to search, analyze, and interact with the content.

## Overview

The MCP server transforms your content collection into an AI-accessible knowledge base that can enhance conversations, provide context-aware assistance, and enable content discovery across various AI applications.

## Prerequisites

1. **MCP Resources**: 
   - For the **default author (`virtual_adrianco`)**: MCP resources are already included in the repository at `mcp_resources/virtual_adrianco/`
   - For **other authors**: Generate MCP resources first:
     ```bash
     python create_mcp.py <author_name>
     ```

2. **Install Dependencies**: The MCP server dependencies are included in the repository:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

1. **Test the Server**:
   ```bash
   python test_mcp_server.py --author <author_name>
   ```

2. **Start the Server (STDIO - Default)**:
   ```bash
   python mcp_server.py --author <author_name>
   ```

3. **Start the Server (HTTP)**:
   ```bash
   python mcp_server.py --author <author_name> --transport streamable-http --port 8080
   ```

4. **Start the Server (SSE - Legacy)**:
   ```bash
   python mcp_server.py --author <author_name> --transport sse --port 8080
   ```

## Server Capabilities

### Tools (AI-Callable Functions)

- **`search_content(query, content_type?, limit?)`**: Search through content by title, tags, or source
- **`get_content_by_id(content_id)`**: Retrieve specific content items by unique ID
- **`get_content_by_type(content_type, limit?)`**: Filter content by type (podcast, book, etc.)
- **`get_content_by_tags(tags, match_all?, limit?)`**: Tag-based content discovery with AND/OR logic
- **`get_content_statistics()`**: Collection analytics and metadata

### Resources (Direct Data Access)

- **`content://metadata`**: Collection metadata and statistics
- **`content://all`**: Complete content listing in summary format
- **`content://types`**: Available content types and counts
- **`content://tags`**: Tag usage statistics and complete tag list

### Prompts (Pre-built Templates)

- **`analyze_content_topic(topic)`**: Deep analysis of content on specific topics
- **`content_recommendation(interest)`**: Personalized content suggestions by interest
- **`content_summary_report()`**: Comprehensive collection analysis

## Integration Examples

### 1. Claude Desktop (STDIO)

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "author-content": {
      "command": "python",
      "args": ["/path/to/meGPT/mcp_server.py", "--author", "your_author_name"],
      "env": {}
    }
  }
}
```

### 2. Cursor IDE (STDIO)

Configure in Cursor settings to enable content-aware coding assistance:

```json
{
  "mcp.servers": [
    {
      "name": "author-content",
      "command": ["python", "/path/to/meGPT/mcp_server.py", "--author", "your_author_name"]
    }
  ]
}
```

### 3. Custom Python Agent (STDIO)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py", "--author", "your_author_name"],
    env=None
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Search for content
        result = await session.call_tool(
            "search_content", 
            arguments={"query": "microservices", "limit": 5}
        )
        print(result.content[0].text)
```

### 4. HTTP Client (Streamable HTTP)

```python
from fastmcp import Client

async def main():
    # Connect to HTTP server
    async with Client("http://localhost:8000/mcp") as client:
        # Search for content
        result = await client.call_tool("search_content", {"query": "microservices", "limit": 5})
        print(result[0].text)
```

### 4. LangGraph Integration

```python
from langgraph import StateGraph
from mcp_client import MCPClient

def create_content_aware_agent(author_name):
    mcp_client = MCPClient("http://localhost:8000")
    
    def search_author_content(state):
        query = state.get("user_query", "")
        results = mcp_client.search_content(query)
        state["content_context"] = results
        return state
    
    graph = StateGraph()
    graph.add_node("search_content", search_author_content)
    # ... rest of agent setup
```

## Use Cases

### Content Discovery
- **Research Assistant**: Find relevant content for specific topics
- **Learning Path**: Get structured recommendations for skill development
- **Cross-Reference**: Connect related content across different formats

### AI Enhancement
- **Context-Aware Chat**: Enhance conversations with domain expertise
- **Code Assistance**: Provide architectural guidance based on the author's experience
- **Technical Writing**: Reference authoritative content for documentation

### Analytics and Insights
- **Content Analysis**: Understand themes and patterns in the collection
- **Gap Analysis**: Identify areas for content expansion
- **Usage Tracking**: Monitor which content is most valuable

## Server Configuration

### Command Line Options

```bash
python mcp_server.py --help
```

- `--author`: Author name for content (default: virtual_adrianco)
- `--transport`: Transport type: stdio, streamable-http, or sse (default: stdio)
- `--port`: Port to run server on for HTTP transports (default: 8000)
- `--host`: Host to run the server on for HTTP transports (default: 127.0.0.1)

### Transport Types

- **STDIO (Default)**: Best for local tools and command-line scripts. Used by Claude Desktop, Cursor, etc.
- **Streamable HTTP**: Recommended for web deployments and remote access
- **SSE**: Legacy web transport (deprecated, use Streamable HTTP instead)

### Environment Variables

- `MCP_AUTHOR`: Default author name
- `MCP_TRANSPORT`: Default transport type
- `MCP_PORT`: Default port number for HTTP transports
- `MCP_HOST`: Default host for HTTP transports
- `MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## API Examples

### Search for Microservices Content (HTTP)

```bash
curl -X POST http://localhost:8000/tools/search_content \
  -H "Content-Type: application/json" \
  -d '{"query": "microservices", "limit": 3}'
```

### Get Content Statistics (HTTP)

```bash
curl -X POST http://localhost:8000/tools/get_content_statistics
```

### Access All Tags (HTTP)

```bash
curl -X GET http://localhost:8000/resources/content://tags
```

## Troubleshooting

### Common Issues

1. **"MCP resource file not found"**
   - Run `python create_mcp.py <author_name>` first
   - Check that `mcp_resources/<author_name>/mcp_resource.json` exists

2. **"Module 'fastmcp' not found"**
   - Install dependencies: `pip install -r requirements.txt`

3. **"Port already in use"**
   - Use a different port: `python mcp_server.py --port 8001`
   - Check for other running servers: `lsof -i :8000`

### Debug Mode

Enable detailed logging:

```bash
export MCP_LOG_LEVEL=DEBUG
python mcp_server.py --author <author_name>
```

### Testing Tools

Use the test script to verify functionality:

```bash
python test_mcp_server.py --author <author_name>
```

## Development

### Adding New Tools

1. Add tool function to `ContentMCPServer._setup_tools()`
2. Use `@self.mcp.tool()` decorator
3. Include proper type hints and docstrings
4. Return JSON-formatted strings

### Adding New Resources

1. Add resource function to `ContentMCPServer._setup_resources()`
2. Use `@self.mcp.resource("uri")` decorator
3. Follow `content://` URI scheme
4. Return JSON-formatted strings

### Adding New Prompts

1. Add prompt function to `ContentMCPServer._setup_prompts()`
2. Use `@self.mcp.prompt()` decorator
3. Include parameter documentation
4. Return formatted prompt strings

## Performance Considerations

- **Memory Usage**: All content is loaded into memory for fast search
- **Concurrent Requests**: FastMCP handles multiple simultaneous connections
- **Response Time**: In-memory search provides sub-second response times
- **Scalability**: Suitable for collections up to ~10,000 content items

## Security Notes

- Server runs on localhost by default (not exposed externally)
- No authentication required for local development
- Content is read-only (no modification capabilities)
- Consider firewall rules for production deployments

## Future Enhancements

- Vector search capabilities for semantic content discovery
- Real-time content updates from source repositories
- Multi-author support with content isolation
- Advanced analytics and usage metrics
- Integration with external knowledge bases

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs for error details
3. Test with the provided test script
4. Verify MCP resource generation completed successfully 