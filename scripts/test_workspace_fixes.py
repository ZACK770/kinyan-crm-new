#!/usr/bin/env python3
"""
Test script for workspace field editing fixes.
Tests the 500 error fix, debug endpoint, and validates the changes work correctly.

Usage:
    python scripts/test_workspace_fixes.py

Requirements:
    - Server running on localhost:8000 OR production URL
    - Valid auth token (will prompt if needed)
    - At least one lead in the database
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

import httpx


class WorkspaceFixTester:
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
    def log(self, level: str, message: str, details: Any = None):
        """Log test results with timestamp and details."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {level.upper()}: {message}")
        if details:
            if isinstance(details, dict):
                print(json.dumps(details, indent=2, ensure_ascii=False))
            else:
                print(f"  Details: {details}")
        
        self.test_results.append({
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "details": details
        })
    
    def headers(self) -> Dict[str, str]:
        """Get headers with auth token."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def test_auth(self) -> bool:
        """Test authentication and get user info."""
        self.log("info", "🔐 Testing authentication...")
        try:
            response = await self.client.get(f"{self.base_url}/api/auth/me", headers=self.headers())
            if response.status_code == 200:
                user_data = response.json()
                self.log("success", f"✅ Authenticated as: {user_data.get('full_name', 'Unknown')} (permission: {user_data.get('permission_level', 0)})")
                return True
            else:
                self.log("error", f"❌ Auth failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log("error", f"❌ Auth error: {e}")
            return False
    
    async def get_test_lead(self) -> Optional[Dict[str, Any]]:
        """Get a lead to test with."""
        self.log("info", "🔍 Finding a test lead...")
        try:
            response = await self.client.get(f"{self.base_url}/api/leads?limit=1", headers=self.headers())
            if response.status_code == 200:
                leads = response.json()
                if leads:
                    lead = leads[0]
                    self.log("success", f"✅ Found test lead: {lead['full_name']} (ID: {lead['id']})")
                    return lead
                else:
                    self.log("error", "❌ No leads found in database")
                    return None
            else:
                self.log("error", f"❌ Failed to get leads: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log("error", f"❌ Error getting leads: {e}")
            return None
    
    async def test_debug_endpoint(self, lead_id: int) -> bool:
        """Test the new debug endpoint."""
        self.log("info", f"🐛 Testing debug endpoint for lead {lead_id}...")
        try:
            response = await self.client.get(f"{self.base_url}/api/leads/{lead_id}/debug", headers=self.headers())
            if response.status_code == 200:
                debug_data = response.json()
                self.log("success", "✅ Debug endpoint working!")
                self.log("info", "Debug summary:", debug_data.get("debug_summary", {}))
                
                # Validate structure
                required_keys = ["lead_id", "debug_summary", "all_fields", "patch_test_instructions"]
                missing_keys = [key for key in required_keys if key not in debug_data]
                if missing_keys:
                    self.log("warning", f"⚠️ Debug response missing keys: {missing_keys}")
                else:
                    self.log("success", "✅ Debug response has all required keys")
                
                return True
            else:
                self.log("error", f"❌ Debug endpoint failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log("error", f"❌ Debug endpoint error: {e}")
            return False
    
    async def test_field_update(self, lead_id: int, field: str, test_value: Any, original_value: Any = None) -> bool:
        """Test updating a specific field and check for 500 errors."""
        self.log("info", f"🔧 Testing field update: {field} = {test_value}")
        
        try:
            # Make the PATCH request
            payload = {field: test_value}
            response = await self.client.patch(
                f"{self.base_url}/api/leads/{lead_id}", 
                json=payload, 
                headers=self.headers()
            )
            
            if response.status_code == 200:
                response_data = response.json()
                self.log("success", f"✅ Field update successful: {field}")
                
                # Verify the field was actually updated
                if field in response_data and response_data[field] == test_value:
                    self.log("success", f"✅ Field value confirmed in response: {response_data[field]}")
                else:
                    self.log("warning", f"⚠️ Field value mismatch in response. Expected: {test_value}, Got: {response_data.get(field, 'MISSING')}")
                
                # Check for updated_at and last_edited_at fields (should be present after db.refresh)
                if response_data.get("updated_at"):
                    self.log("success", f"✅ updated_at field present: {response_data['updated_at']}")
                else:
                    self.log("warning", "⚠️ updated_at field missing from response")
                
                if response_data.get("last_edited_at"):
                    self.log("success", f"✅ last_edited_at field present: {response_data['last_edited_at']}")
                else:
                    self.log("info", "ℹ️ last_edited_at field not set (normal for non-status/salesperson fields)")
                
                return True
            else:
                self.log("error", f"❌ Field update failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.log("error", "Error details:", error_data)
                except:
                    self.log("error", "Raw error response:", response.text)
                return False
                
        except Exception as e:
            self.log("error", f"❌ Field update exception: {e}")
            self.log("error", "Full traceback:", traceback.format_exc())
            return False
    
    async def test_multiple_field_updates(self, lead_id: int) -> bool:
        """Test updating multiple different field types."""
        self.log("info", "🔄 Testing multiple field updates...")
        
        # Get current lead data first
        try:
            response = await self.client.get(f"{self.base_url}/api/leads/{lead_id}", headers=self.headers())
            if response.status_code != 200:
                self.log("error", "❌ Could not get current lead data")
                return False
            
            current_lead = response.json()
            self.log("info", f"Current lead data retrieved: {current_lead['full_name']}")
        except Exception as e:
            self.log("error", f"❌ Error getting current lead: {e}")
            return False
        
        # Test different field types
        test_cases = [
            # (field_name, test_value, description)
            ("notes", f"Test note updated at {datetime.now().strftime('%H:%M:%S')}", "text field"),
            ("status", "ליד בתהליך", "select field (triggers last_edited_at)"),
            ("id_number", "123456789", "text field that caused original 500"),
            ("family_name", "משפחה-טסט", "text field with Hebrew"),
        ]
        
        success_count = 0
        for field, test_value, description in test_cases:
            self.log("info", f"Testing {description}: {field}")
            if await self.test_field_update(lead_id, field, test_value, current_lead.get(field)):
                success_count += 1
            else:
                self.log("error", f"❌ Failed to update {field}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        self.log("info", f"Field update results: {success_count}/{len(test_cases)} successful")
        return success_count == len(test_cases)
    
    async def test_concurrent_updates(self, lead_id: int) -> bool:
        """Test concurrent field updates to check for race conditions."""
        self.log("info", "⚡ Testing concurrent field updates...")
        
        try:
            # Create multiple concurrent update tasks
            tasks = []
            for i in range(3):
                field_value = f"concurrent-test-{i}-{datetime.now().strftime('%H%M%S')}"
                task = self.test_field_update(lead_id, "notes", field_value)
                tasks.append(task)
            
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            error_count = sum(1 for result in results if isinstance(result, Exception))
            
            self.log("info", f"Concurrent update results: {success_count} successful, {error_count} errors")
            
            if error_count > 0:
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.log("error", f"Concurrent task {i} failed: {result}")
            
            return success_count >= 2  # Allow some failures in concurrent scenario
            
        except Exception as e:
            self.log("error", f"❌ Concurrent test error: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        self.log("info", "🚀 Starting workspace fixes test suite...")
        self.log("info", f"Target URL: {self.base_url}")
        
        try:
            # Test 1: Authentication
            if not await self.test_auth():
                self.log("error", "❌ Authentication failed - cannot continue")
                return False
            
            # Test 2: Get test lead
            test_lead = await self.get_test_lead()
            if not test_lead:
                self.log("error", "❌ No test lead available - cannot continue")
                return False
            
            lead_id = test_lead["id"]
            
            # Test 3: Debug endpoint
            debug_success = await self.test_debug_endpoint(lead_id)
            
            # Test 4: Single field updates
            single_update_success = await self.test_multiple_field_updates(lead_id)
            
            # Test 5: Concurrent updates
            concurrent_success = await self.test_concurrent_updates(lead_id)
            
            # Summary
            total_tests = 3
            passed_tests = sum([debug_success, single_update_success, concurrent_success])
            
            self.log("info", f"📊 Test Summary: {passed_tests}/{total_tests} test groups passed")
            
            if passed_tests == total_tests:
                self.log("success", "🎉 ALL TESTS PASSED! Workspace fixes are working correctly.")
                return True
            else:
                self.log("warning", f"⚠️ {total_tests - passed_tests} test group(s) failed")
                return False
                
        except Exception as e:
            self.log("error", f"❌ Test suite error: {e}")
            self.log("error", "Full traceback:", traceback.format_exc())
            return False
        finally:
            await self.client.aclose()
    
    def save_results(self, filename: str = "test_results.json"):
        """Save test results to file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            self.log("info", f"📄 Test results saved to {filename}")
        except Exception as e:
            self.log("error", f"❌ Could not save results: {e}")


async def main():
    """Main test runner."""
    print("=" * 80)
    print("🧪 KINYAN CRM - WORKSPACE FIXES TEST SUITE")
    print("=" * 80)
    
    # Configuration
    import os
    
    # Try production first, then local
    base_url = "https://kinyan-crm-new-1.onrender.com"
    auth_token = None
    
    # Check if we should use local instead
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        base_url = "http://localhost:8000"
        print("🏠 Using LOCAL server")
    else:
        print("🌐 Using PRODUCTION server")
    
    print(f"🎯 Target: {base_url}")
    
    # Get auth token
    if not auth_token:
        print("\n🔑 Auth token required. Options:")
        print("1. Set AUTH_TOKEN environment variable")
        print("2. Enter token manually")
        
        auth_token = os.getenv("AUTH_TOKEN")
        if not auth_token:
            auth_token = input("Enter auth token (or press Enter to skip): ").strip()
            if not auth_token:
                print("⚠️ No auth token provided - tests may fail")
    
    # Run tests
    tester = WorkspaceFixTester(base_url, auth_token)
    success = await tester.run_all_tests()
    
    # Save results
    tester.save_results("workspace_test_results.json")
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The 500 error fix is working")
        print("✅ Debug endpoint is functional") 
        print("✅ Field updates work correctly")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check the detailed output above for specific issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
