"""
Comprehensive HTTP Streaming MCP Server Test

This script tests the MCP server running in HTTP streaming mode by connecting
as a client and testing various tools and resources. It demonstrates all the
major functionality of the meGPT MCP server.

Prerequisites:
1. Start the MCP server in HTTP mode:
   python mcp_server.py --author virtual_adrianco --transport streamable-http --port 8080

2. Ensure dependencies are installed:
   pip install -r requirements.txt

Usage:
   python mcp_testing/test_http_client.py

Expected Results:
- Connection to MCP server at http://localhost:8080/mcp
- Discovery of 5 tools, 4 resources, and 3 prompts
- Successful execution of content search, statistics, and prompt generation
- Real data from virtual_adrianco collection (216+ items)
"""

import asyncio
import sys
from fastmcp import Client

async def test_http_mcp_server():
    """Test the HTTP streaming MCP server with comprehensive functionality checks"""
    
    server_url = "http://localhost:8080/mcp"
    print(f"🔗 Testing MCP server at {server_url}")
    print("=" * 60)
    
    try:
        # Create client for HTTP server
        client = Client(server_url)
        
        async with client:
            print("✅ Successfully connected to MCP server\n")
            
            # Test 1: List available tools
            print("🔧 1. Testing tool listing...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description[:80]}{'...' if len(tool.description) > 80 else ''}")
            
            # Test 2: Search content
            print(f"\n🔍 2. Testing content search...")
            result = await client.call_tool("search_content", {
                "query": "microservices",
                "limit": 3
            })
            print("✅ Search results for 'microservices':")
            search_data = result[0].text
            print(f"   Preview: {search_data[:200]}{'...' if len(search_data) > 200 else ''}")
            
            # Test 3: Get content statistics
            print(f"\n📊 3. Testing content statistics...")
            stats_result = await client.call_tool("get_content_statistics")
            print("✅ Statistics retrieved:")
            stats_data = stats_result[0].text
            print(f"   Preview: {stats_data[:300]}{'...' if len(stats_data) > 300 else ''}")
            
            # Test 4: List resources
            print(f"\n📁 4. Testing resource listing...")
            resources = await client.list_resources()
            print(f"✅ Found {len(resources)} resources:")
            for resource in resources:
                description = resource.description or "Direct data access"
                print(f"   - {resource.uri}: {description}")
            
            # Test 5: Read a resource
            print(f"\n📖 5. Testing resource reading...")
            metadata = await client.read_resource("content://metadata")
            print("✅ Metadata resource accessed:")
            metadata_text = metadata[0].text
            print(f"   Preview: {metadata_text[:200]}{'...' if len(metadata_text) > 200 else ''}")
            
            # Test 6: List prompts
            print(f"\n💬 6. Testing prompt listing...")
            prompts = await client.list_prompts()
            print(f"✅ Found {len(prompts)} prompts:")
            for prompt in prompts:
                print(f"   - {prompt.name}: {prompt.description[:80]}{'...' if len(prompt.description) > 80 else ''}")
            
            # Test 7: Get a prompt
            print(f"\n🎯 7. Testing prompt generation...")
            prompt_result = await client.get_prompt("analyze_content_topic", {
                "topic": "cloud architecture"
            })
            print("✅ Generated analysis prompt for 'cloud architecture':")
            prompt_text = prompt_result.messages[0].content.text
            print(f"   Preview: {prompt_text[:200]}{'...' if len(prompt_text) > 200 else ''}")
            
            print("\n" + "=" * 60)
            print("🎉 All HTTP streaming tests passed successfully!")
            print("\nThe MCP server is fully functional and ready for:")
            print("   • AI application integration")
            print("   • Content-aware chatbots")
            print("   • Development tool enhancement")
            print("   • Custom agent workflows")
            return True
            
    except Exception as e:
        print(f"❌ Error testing HTTP MCP server: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure the MCP server is running:")
        print("   python mcp_server.py --author virtual_adrianco --transport streamable-http --port 8080")
        print("2. Check that virtual_adrianco MCP resources exist")
        print("3. Verify dependencies: pip install -r requirements.txt")
        return False

async def main():
    """Main test execution"""
    print("MCP Server Comprehensive Test Suite")
    print("Testing HTTP streaming functionality with real content data\n")
    
    success = await test_http_mcp_server()
    
    if success:
        print(f"\n✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Test suite failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 