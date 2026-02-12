#!/usr/bin/env python3
"""Test script to verify Orchestrator and all MCP server connections."""

import asyncio
import httpx
import sys


async def test_jenkins_mcp():
    """Test if Jenkins MCP server is running."""
    print("\n🔍 Testing Jenkins MCP Server (port 8000)...")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/sse", timeout=2.0)
            print(f"✗ Unexpected response: {response.status_code}")
            return False
    except httpx.ReadTimeout:
        print("✓ Jenkins MCP server is running (SSE endpoint responding)")
        return True
    except httpx.ConnectError:
        print("✗ Jenkins MCP server is NOT running on http://localhost:8000")
        print("  → Run: cd Jenkins_MCP && jenkins-mcp-server")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_kubernetes_mcp():
    """Test if Kubernetes MCP server is running."""
    print("\n🔍 Testing Kubernetes MCP Server (port 8001)...")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8001/sse", timeout=2.0)
            print(f"✗ Unexpected response: {response.status_code}")
            return False
    except httpx.ReadTimeout:
        print("✓ Kubernetes MCP server is running (SSE endpoint responding)")
        return True
    except httpx.ConnectError:
        print("✗ Kubernetes MCP server is NOT running on http://localhost:8001")
        print("  → Run: cd Kubernetes_MCP && kubernetes-mcp-server")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_orchestrator():
    """Test if Orchestrator server is running."""
    print("\n🔍 Testing Orchestrator Server (port 8080)...")
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
        print(f"✗ Error: {e}")
        return False


async def test_mcp_configurations():
    """Test MCP server configurations in Orchestrator."""
    print("\n🔍 Testing MCP Server Configurations...")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8080/servers")
            
            if response.status_code == 200:
                data = response.json()
                servers = data.get('servers', [])
                
                for server in servers:
                    status = "✓" if server['enabled'] else "○"
                    print(f"  {status} {server['name']}: {server['url']}")
                
                return len(servers) > 0
            else:
                print(f"✗ Failed to get servers: {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_chat(message: str = "What tools do you have available?"):
    """Test a chat with the Orchestrator."""
    print(f"\n🔍 Testing Chat: '{message[:50]}...'")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8080/chat",
                json={
                    "message": message,
                    "user_id": "test_user",
                    "session_id": "test_session_all"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                resp_text = data.get('response', '')
                print(f"✓ Chat response received ({len(resp_text)} chars)")
                # Show preview
                preview = resp_text[:300].replace('\n', ' ')
                print(f"  → {preview}..." if len(resp_text) > 300 else f"  → {preview}")
                return True
            else:
                print(f"✗ Chat failed: {response.status_code}")
                return False
    except httpx.ReadTimeout:
        print("✗ Chat request timed out")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("  ORCHESTRATOR & ALL MCP SERVERS CONNECTION TEST")
    print("=" * 60)
    
    results = {}
    
    # Test Jenkins MCP
    results['jenkins_mcp'] = await test_jenkins_mcp()
    
    # Test Kubernetes MCP
    results['kubernetes_mcp'] = await test_kubernetes_mcp()
    
    # Test Orchestrator
    results['orchestrator'] = await test_orchestrator()
    
    # Test MCP configurations
    if results['orchestrator']:
        results['mcp_config'] = await test_mcp_configurations()
    else:
        results['mcp_config'] = False
    
    # Test Chat (only if orchestrator is running)
    if results['orchestrator']:
        results['chat'] = await test_chat()
    else:
        print("\n⚠️  Skipping chat test - Orchestrator not running")
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
        print("\nYou can now use the Orchestrator to:")
        print("  • Manage Jenkins jobs and builds")
        print("  • Manage Kubernetes pods, deployments, and services")
        print("  • Ask general questions")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        print("\nTo start all services:")
        print("  Terminal 1: cd Jenkins_MCP && jenkins-mcp-server")
        print("  Terminal 2: cd Kubernetes_MCP && kubernetes-mcp-server")
        print("  Terminal 3: cd Orchestrator && orchestrator serve")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))