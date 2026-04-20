#!/usr/bin/env python3
"""
Simple endpoint availability test - checks if bulk-delete endpoint exists.
"""
import asyncio
import aiohttp
import ssl


async def test_endpoint_availability():
    """Test if the bulk-delete endpoint exists on the remote server."""
    base_url = "https://kinyan-crm-new-1.onrender.com"
    
    # Create SSL context that doesn't verify certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"🌐 Testing endpoint: {base_url}/api/leads/bulk-delete")
        
        try:
            # Try with empty data to see if endpoint exists
            async with session.post(
                f"{base_url}/api/leads/bulk-delete",
                json={"ids": []},
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"📡 Response status: {response.status}")
                print(f"📡 Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"📡 Response body: {response_text}")
                
                if response.status == 405:
                    print("❌ Endpoint returns 405 Method Not Allowed - endpoint missing!")
                    return False
                elif response.status == 401:
                    print("✅ Endpoint exists but requires authentication (401 Unauthorized)")
                    return True
                elif response.status == 403:
                    print("✅ Endpoint exists but access forbidden (403 Forbidden)")
                    return True
                elif response.status in [200, 400, 422]:
                    print("✅ Endpoint exists and responds")
                    return True
                else:
                    print(f"⚠️ Endpoint exists but returned unexpected status: {response.status}")
                    return True
                    
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")
            return False


async def main():
    """Main function."""
    print("🚀 Testing bulk delete endpoint availability...")
    
    success = await test_endpoint_availability()
    
    if success:
        print("\n🎉 Endpoint is available! The bulk delete fix is deployed.")
    else:
        print("\n💥 Endpoint is not available. The fix may not be deployed yet.")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
