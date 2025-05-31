"""
Test Script for MCP Server

Purpose:
This script tests the MCP server functionality by loading content and verifying
that all components work correctly without starting the actual HTTP server.

Usage:
    python test_mcp_server.py [--author AUTHOR]
"""

import sys
from pathlib import Path
from mcp_server import ContentMCPServer

def test_mcp_server(author: str = "virtual_adrianco"):
    """Test MCP server functionality"""
    
    print(f"Testing MCP server for author: {author}")
    
    # Check if MCP resource exists
    mcp_file = Path(f"mcp_resources/{author}/mcp_resource.json")
    if not mcp_file.exists():
        print(f"Error: MCP resource file not found at {mcp_file}")
        print("Please run create_mcp.py first to generate the MCP resource.")
        return False
    
    try:
        # Create server instance (this loads and validates content)
        server = ContentMCPServer(author=author)
        
        print(f"✓ Successfully loaded {len(server.content_items)} content items")
        
        # Test basic functionality
        if server.content_items:
            sample_item = server.content_items[0]
            print(f"✓ Sample content item: {sample_item.title} ({sample_item.kind})")
            
            # Test content types
            content_types = set(item.kind for item in server.content_items)
            print(f"✓ Found {len(content_types)} content types: {', '.join(sorted(content_types))}")
            
            # Test tags
            all_tags = set()
            for item in server.content_items:
                all_tags.update(item.tags)
            print(f"✓ Found {len(all_tags)} unique tags")
            
            # Test metadata
            metadata = server.content_data.get('metadata', {})
            print(f"✓ Metadata loaded: {metadata.get('content_count', 0)} items, version {metadata.get('version', 'unknown')}")
            
        print("\n✓ All tests passed! MCP server is ready to run.")
        print(f"To start the server, run: python mcp_server.py --author {author}")
        return True
        
    except Exception as e:
        print(f"✗ Error testing MCP server: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP Server")
    parser.add_argument("--author", default="virtual_adrianco", 
                       help="Author name for content (default: virtual_adrianco)")
    
    args = parser.parse_args()
    
    success = test_mcp_server(args.author)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 