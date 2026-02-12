#!/usr/bin/env python3
"""Test script to verify Orchestrator and Jenkins MCP connection."""

import asyncio
import httpx
import sys


async def test_jenkins_mcp():
    """Test if Jenkins MCP server is running."""
    print("\n🔍 Testing Jenkins MCP Server...")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to connect to the SSE endpoint
            response = await client.get("http://localhost:8000/sse", timeout=2.0)
            print(f"✗ Unexpected response from Jenkins MCP: {response.status_code}")
            return False
    except httpx.ReadTimeout:
        # SSE endpoints typically hang waiting for events - this is expected!
        print("✓ Jenkins MCP server is running (SSE endpoint responding)")
        return True
    except httpx.ConnectError:
        print("✗ Jenkins MCP server is NOT running on http://localhost:8000")
        print("  → Run: cd Jenkins_MCP && jenkins-mcp-server")
        return False
    except Exception as e:
        print(f"✗ Error connecting to Jenkins MCP: {e}")
        return False


async def test_orchestrator():
    """Test if Orchestrator server is running."""
    print("\n🔍 Testing Orchestrator Server...")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8080/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Orchestrator is running")
                print(f"  → Status: {data.get('status', 'unknown')}")
                print(f"  → Model: {data.get('model', 'unknown')}")
                print(f"  → MCP Servers: {data.get('mcp_servers', [])}")
                return True
            else:
                print(f"✗ Orchestrator returned status {response.status_code}")
                return False
    except httpx.ConnectError:
        print("✗ Orchestrator is NOT running on http://localhost:8080")
        print("  → Run: cd Orchestrator && orchestrator serve")
        return False
    except Exception as e:
        print(f"✗ Error connecting to Orchestrator: {e}")
        return False


async def test_orchestrator_mcp_connection():
    """Test if Orchestrator is connected to Jenkins MCP."""
    print("\n🔍 Testing Orchestrator → Jenkins MCP Connection...")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8080/servers")
            
            if response.status_code == 200:
                data = response.json()
                servers = data.get('servers', [])
                
                jenkins_server = next((s for s in servers if s['name'] == 'jenkins'), None)
                
                if jenkins_server:
                    print(f"✓ Jenkins MCP configured in Orchestrator")
                    print(f"  → URL: {jenkins_server['url']}")
                    print(f"  → Transport: {jenkins_server['transport']}")
                    print(f"  → Enabled: {jenkins_server['enabled']}")
                    return True
                else:
                    print("✗ Jenkins MCP not found in Orchestrator configuration")
                    return False
            else:
                print(f"✗ Failed to get servers: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_chat():
    """Test a simple chat with the Orchestrator."""
    print("\n🔍 Testing Chat Functionality...")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # First, a simple greeting
            response = await client.post(
                "http://localhost:8080/chat",
                json={
                    "message": "Hello, what tools do you have available?",
                    "user_id": "test_user",
                    "session_id": "test_session"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                resp_text = data.get('response', '')
                print(f"✓ Chat response received ({len(resp_text)} chars)")
                print(f"  → Preview: {resp_text[:200]}..." if len(resp_text) > 200 else f"  → Response: {resp_text}")
                return True
            else:
                error = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"✗ Chat failed with status {response.status_code}")
                print(f"  → Error: {error}")
                return False
    except httpx.ReadTimeout:
        print("✗ Chat request timed out (60s)")
        print("  → The agent might be taking too long to respond")
        return False
    except Exception as e:
        print(f"✗ Error during chat: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("  ORCHESTRATOR & JENKINS MCP CONNECTION TEST")
    print("=" * 60)
    
    results = {}
    
    # Test Jenkins MCP
    results['jenkins_mcp'] = await test_jenkins_mcp()
    
    # Test Orchestrator
    results['orchestrator'] = await test_orchestrator()
    
    # Test MCP Connection config
    if results['orchestrator']:
        results['mcp_config'] = await test_orchestrator_mcp_connection()
    else:
        results['mcp_config'] = False
    
    # Test Chat (only if both are running)
    if results['jenkins_mcp'] and results['orchestrator']:
        results['chat'] = await test_chat()
    else:
        print("\n⚠️  Skipping chat test - services not running")
        results['chat'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\nTo fix common issues:")
        print("  1. Start Jenkins MCP: cd Jenkins_MCP && jenkins-mcp-server")
        print("  2. Start Orchestrator: cd Orchestrator && orchestrator serve")
        print("  3. Ensure GOOGLE_API_KEY is set in Orchestrator/.env")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))