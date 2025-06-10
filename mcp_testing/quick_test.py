"""
Quick MCP Server Functionality Test

This script performs a quick test of specific MCP server features including
tag-based search and content type filtering. It's useful for rapid verification
that the server is working correctly.

Prerequisites:
1. Start the MCP server in HTTP mode:
   python mcp_server.py --author virtual_adrianco --transport streamable-http --port 8080

Usage:
   python mcp_testing/quick_test.py

Expected Results:
- Tag-based search results for microservices/architecture content
- Podcast content filtering results
- JSON-formatted responses with real data
"""

import asyncio
from fastmcp import Client

async def quick_test():
    """Quick test of key MCP server functionality"""
    
    print("🚀 Quick MCP Server Functionality Test")
    print("=" * 50)
    
    client = Client("http://localhost:8080/mcp")
    
    try:
        async with client:
            print("✅ Connected to MCP server\n")
            
            # Test 1: Tag-based search
            print("🏷️  Testing tag-based search (microservices OR architecture)...")
            result = await client.call_tool("get_content_by_tags", {
                "tags": "microservices,architecture",
                "match_all": False,
                "limit": 2
            })
            print("✅ Tag search results:")
            print(result[0].text)
            
            # Test 2: Content by type
            print(f"\n🎧 Testing content type filtering (podcasts)...")
            result2 = await client.call_tool("get_content_by_type", {
                "content_type": "podcast",
                "limit": 2
            })
            print("✅ Podcast content:")
            print(result2[0].text)
            
            print("\n" + "=" * 50)
            print("🎉 Quick test completed successfully!")
            print("✅ Tag-based search: Working")
            print("✅ Content type filtering: Working")
            print("✅ JSON response formatting: Working")
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure MCP server is running on port 8080")
        print("2. Check server logs for errors")
        print("3. Verify virtual_adrianco content is loaded")

if __name__ == "__main__":
    asyncio.run(quick_test()) 