#!/usr/bin/env python3
"""
Remote debugging script for bulk delete functionality.
Tests the bulk delete endpoint directly on the remote server.
"""
import asyncio
import aiohttp
import json
import ssl
from typing import Dict, Any, List


class RemoteBulkDeleteTester:
    def __init__(self, base_url: str = "https://kinyan-crm-new-1.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.auth_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self, email: str, password: str) -> bool:
        """Login and get authentication token."""
        login_data = {
            "username": email,
            "password": password
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    print(f"✅ Login successful for {email}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def create_test_leads(self, count: int = 3) -> List[int]:
        """Create test leads for deletion testing."""
        created_ids = []
        
        for i in range(count):
            lead_data = {
                "full_name": f"Test Lead {i+1} - DELETE ME",
                "phone": f"050000000{i+1}",
                "email": f"test{i+1}@delete.me",
                "source_type": "test",
                "source_name": "bulk_delete_test",
                "notes": "Created by remote debugging script - safe to delete"
            }
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/leads/",
                    headers=self.get_headers(),
                    json=lead_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        lead_id = result.get("lead_id")
                        if lead_id:
                            created_ids.append(lead_id)
                            print(f"✅ Created test lead #{lead_id}: {lead_data['full_name']}")
                        else:
                            print(f"⚠️ Lead created but no ID returned: {result}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create test lead {i+1}: {response.status} - {error_text}")
            except Exception as e:
                print(f"❌ Error creating test lead {i+1}: {e}")
        
        return created_ids
    
    async def test_bulk_delete_endpoint(self, lead_ids: List[int]) -> Dict[str, Any]:
        """Test the bulk delete endpoint."""
        if not lead_ids:
            return {"success": False, "error": "No lead IDs provided"}
        
        delete_data = {"ids": lead_ids}
        
        try:
            print(f"🧪 Testing bulk delete with IDs: {lead_ids}")
            async with self.session.post(
                f"{self.base_url}/api/leads/bulk-delete",
                headers=self.get_headers(),
                json=delete_data
            ) as response:
                response_text = await response.text()
                
                print(f"📡 Response status: {response.status}")
                print(f"📡 Response headers: {dict(response.headers)}")
                print(f"📡 Response body: {response_text}")
                
                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        print(f"✅ Bulk delete successful: {result}")
                        return result
                    except json.JSONDecodeError:
                        print(f"⚠️ Success but invalid JSON response: {response_text}")
                        return {"success": True, "raw_response": response_text}
                else:
                    print(f"❌ Bulk delete failed: {response.status}")
                    try:
                        error_data = json.loads(response_text)
                        return {"success": False, "error": error_data, "status": response.status}
                    except json.JSONDecodeError:
                        return {"success": False, "error": response_text, "status": response.status}
                        
        except Exception as e:
            print(f"❌ Exception during bulk delete test: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_leads_deleted(self, lead_ids: List[int]) -> Dict[str, Any]:
        """Verify that the leads were actually deleted."""
        verification_results = {}
        
        for lead_id in lead_ids:
            try:
                async with self.session.get(
                    f"{self.base_url}/api/leads/{lead_id}",
                    headers=self.get_headers()
                ) as response:
                    if response.status == 404:
                        verification_results[lead_id] = "deleted"
                        print(f"✅ Lead #{lead_id} confirmed deleted (404)")
                    elif response.status == 200:
                        verification_results[lead_id] = "still_exists"
                        print(f"❌ Lead #{lead_id} still exists!")
                    else:
                        verification_results[lead_id] = f"unknown_status_{response.status}"
                        print(f"⚠️ Lead #{lead_id} verification returned {response.status}")
            except Exception as e:
                verification_results[lead_id] = f"error: {e}"
                print(f"❌ Error verifying lead #{lead_id}: {e}")
        
        return verification_results
    
    async def test_endpoint_availability(self) -> bool:
        """Test if the bulk-delete endpoint exists."""
        try:
            # Try with empty data to see if endpoint exists
            async with self.session.post(
                f"{self.base_url}/api/leads/bulk-delete",
                headers=self.get_headers(),
                json={"ids": []}
            ) as response:
                if response.status == 405:
                    print("❌ Endpoint returns 405 Method Not Allowed - endpoint missing!")
                    return False
                elif response.status in [200, 400, 422]:
                    print("✅ Endpoint exists and responds")
                    return True
                else:
                    print(f"⚠️ Endpoint exists but returned unexpected status: {response.status}")
                    return True
        except Exception as e:
            print(f"❌ Error testing endpoint availability: {e}")
            return False
    
    async def run_full_test(self, email: str, password: str) -> Dict[str, Any]:
        """Run the complete bulk delete test suite."""
        print("🚀 Starting remote bulk delete test...")
        print(f"🌐 Target server: {self.base_url}")
        
        # Step 1: Login
        if not await self.login(email, password):
            return {"success": False, "error": "Login failed"}
        
        # Step 2: Test endpoint availability
        print("\n📡 Testing endpoint availability...")
        if not await self.test_endpoint_availability():
            return {"success": False, "error": "Bulk delete endpoint not available"}
        
        # Step 3: Create test leads
        print("\n🏗️ Creating test leads...")
        test_lead_ids = await self.create_test_leads(3)
        if not test_lead_ids:
            return {"success": False, "error": "Failed to create test leads"}
        
        # Step 4: Test bulk delete
        print("\n🗑️ Testing bulk delete...")
        delete_result = await self.test_bulk_delete_endpoint(test_lead_ids)
        
        # Step 5: Verify deletion
        print("\n🔍 Verifying deletion...")
        verification_result = await self.verify_leads_deleted(test_lead_ids)
        
        # Summary
        all_deleted = all(status == "deleted" for status in verification_result.values())
        
        final_result = {
            "success": delete_result.get("success", False) and all_deleted,
            "delete_result": delete_result,
            "verification_result": verification_result,
            "test_lead_ids": test_lead_ids,
            "all_leads_deleted": all_deleted
        }
        
        print("\n📊 Test Summary:")
        print(f"   Delete API Success: {delete_result.get('success', False)}")
        print(f"   All Leads Deleted: {all_deleted}")
        print(f"   Overall Success: {final_result['success']}")
        
        return final_result


async def main():
    """Main function to run the test."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_bulk_delete_remote.py <email> <password> [server_url]")
        print("Example: python test_bulk_delete_remote.py admin@kinyan.com mypassword")
        print("Example: python test_bulk_delete_remote.py admin@kinyan.com mypassword https://kinyan-crm-new-1.onrender.com")
        return
    
    email = sys.argv[1]
    password = sys.argv[2]
    server_url = sys.argv[3] if len(sys.argv) > 3 else "https://kinyan-crm-new-1.onrender.com"
    
    async with RemoteBulkDeleteTester(server_url) as tester:
        result = await tester.run_full_test(email, password)
        
        if result["success"]:
            print("\n🎉 All tests passed! Bulk delete is working correctly.")
            sys.exit(0)
        else:
            print(f"\n💥 Tests failed: {result}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
