# MCP Testing Directory

This directory contains test scripts and documentation for the meGPT MCP server.

## Quick Start

### 1. Basic Functionality Test (Recommended First Step)

Test server functionality without starting HTTP server:

```bash
# Test default author
python mcp_testing/test_mcp_server.py

# Test specific author  
python mcp_testing/test_mcp_server.py --author your_author_name
```

This is the fastest way to verify your MCP setup is working correctly.

### 2. HTTP Streaming Tests

For comprehensive testing with actual HTTP requests:

```bash
# Start server in background
python mcp_server.py --author virtual_adrianco --transport streamable-http --port 8080 &

# Run comprehensive test suite
python mcp_testing/test_http_client.py

# Or run quick functionality test
python mcp_testing/quick_test.py

# Stop background server
kill %1
```

## Test Scripts

### `test_mcp_server.py`
- **Purpose**: Basic functionality validation without HTTP server
- **Speed**: Fastest (< 2 seconds)
- **Use Case**: Setup verification, debugging, health checks
- **Output**: Content statistics, server readiness confirmation

### `test_http_client.py` 
- **Purpose**: Comprehensive HTTP streaming protocol testing
- **Speed**: Moderate (requires server startup)
- **Use Case**: Full integration testing, protocol compliance
- **Output**: Detailed test results with JSON responses

### `quick_test.py`
- **Purpose**: Focused functionality testing
- **Speed**: Fast
- **Use Case**: CI/CD pipelines, specific feature validation
- **Output**: Minimal success/failure indicators

## Documentation

- `MCP_TESTING_GUIDE.md` - Complete testing guide with examples and real output
- `README.md` - This quick start guide

## Prerequisites

1. MCP resources must exist for the author you're testing
2. Dependencies installed: `pip install -r requirements.txt`
3. For default `virtual_adrianco` author, resources are already included

## Test Coverage

The tests verify:
- ✅ Server connection and initialization
- ✅ All 5 MCP tools (search, filtering, statistics)
- ✅ All 4 MCP resources (metadata, content, types, tags)
- ✅ All 3 MCP prompts (analysis, recommendations, reports)
- ✅ HTTP streaming transport functionality
- ✅ JSON response formatting and validation
- ✅ Error handling and edge cases

## Expected Results

When tests pass, you should see:
- Successful connection to MCP server
- 5 tools discovered and tested
- 4 resources accessed successfully
- 3 prompts generated correctly
- Real content data from virtual_adrianco collection (611 items)
- Sub-second response times for all operations

## Troubleshooting

- **Import errors**: Ensure you're running from the project root directory
- **Missing resources**: Run `python create_mcp.py --author <name>` first
- **Connection issues**: Check if server is running on correct port

For detailed examples and results, see `MCP_TESTING_GUIDE.md`. 