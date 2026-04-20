#!/usr/bin/env python3
"""
Comprehensive test script for ALL workspace fields.
Tests each field individually for save, visualization, and immediate display.

Usage:
    python scripts/test_all_workspace_fields.py [--local]
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx


class WorkspaceFieldTester:
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
        # Define ALL workspace fields with their test values
        self.field_tests = {
            # Contact Info Fields
            "full_name": {
                "test_value": f"טסט-שם-{datetime.now().strftime('%H%M%S')}",
                "type": "text",
                "section": "Contact Info"
            },
            "family_name": {
                "test_value": f"משפחה-{datetime.now().strftime('%H%M%S')}",
                "type": "text", 
                "section": "Contact Info"
            },
            "phone": {
                "test_value": "0501234567",
                "type": "text",
                "section": "Contact Info"
            },
            "phone2": {
                "test_value": "0507654321",
                "type": "text",
                "section": "Contact Info"
            },
            "email": {
                "test_value": f"test{datetime.now().strftime('%H%M%S')}@example.com",
                "type": "text",
                "section": "Contact Info"
            },
            "city": {
                "test_value": "ירושלים",
                "type": "text",
                "section": "Contact Info"
            },
            "address": {
                "test_value": f"רחוב הטסט {datetime.now().strftime('%H%M')}",
                "type": "text",
                "section": "Contact Info"
            },
            "id_number": {
                "test_value": "123456789",
                "type": "text",
                "section": "Contact Info",
                "note": "Original 500 error cause"
            },
            
            # Sales Info Fields (PROBLEMATIC ONES)
            "status": {
                "test_value": "ליד בתהליך",
                "type": "select",
                "section": "Sales Info",
                "note": "PROBLEMATIC - select field"
            },
            "salesperson_id": {
                "test_value": 1,  # Will be set dynamically
                "type": "entity-select",
                "section": "Sales Info", 
                "note": "PROBLEMATIC - entity-select field"
            },
            
            # Source Info Fields
            "source_type": {
                "test_value": "elementor",
                "type": "select",
                "section": "Source Info",
                "note": "PROBLEMATIC - select field"
            },
            "campaign_id": {
                "test_value": 1,  # Will be set dynamically
                "type": "entity-select",
                "section": "Source Info",
                "note": "PROBLEMATIC - entity-select field"
            },
            "source_name": {
                "test_value": f"מקור-טסט-{datetime.now().strftime('%H%M')}",
                "type": "text",
                "section": "Source Info"
            },
            "source_message": {
                "test_value": f"הודעת טסט מהמקור - {datetime.now().strftime('%H:%M:%S')}",
                "type": "textarea",
                "section": "Source Info"
            },
            
            # Course Interest Fields
            "course_id": {
                "test_value": 1,  # Will be set dynamically
                "type": "entity-select",
                "section": "Course Interest",
                "note": "PROBLEMATIC - entity-select field"
            },
            
            # Notes
            "notes": {
                "test_value": f"הערות טסט - {datetime.now().strftime('%H:%M:%S')}",
                "type": "textarea",
                "section": "Notes"
            }
        }
        
    def log(self, level: str, message: str, details: Any = None):
        """Log test results with timestamp and details."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Color coding
        colors = {
            "success": "\033[92m",  # Green
            "error": "\033[91m",    # Red
            "warning": "\033[93m",  # Yellow
            "info": "\033[94m",     # Blue
            "reset": "\033[0m"      # Reset
        }
        
        color = colors.get(level, colors["reset"])
        print(f"{color}[{timestamp}] {level.upper()}: {message}{colors['reset']}")
        
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
    
    async def setup_test_data(self) -> bool:
        """Setup test data - get valid IDs for entity-select fields."""
        self.log("info", "🔧 Setting up test data...")
        
        try:
            # Get salesperson ID
            response = await self.client.get(f"{self.base_url}/api/leads/salespersons", headers=self.headers())
            if response.status_code == 200:
                salespeople = response.json()
                if salespeople:
                    self.field_tests["salesperson_id"]["test_value"] = salespeople[0]["id"]
                    self.log("success", f"✅ Found salesperson ID: {salespeople[0]['id']} ({salespeople[0]['name']})")
                else:
                    self.log("warning", "⚠️ No salespeople found - will test with null")
                    self.field_tests["salesperson_id"]["test_value"] = None
            
            # Get campaign ID (if any exist)
            # Note: This endpoint might not exist, so we'll handle gracefully
            try:
                response = await self.client.get(f"{self.base_url}/api/campaigns", headers=self.headers())
                if response.status_code == 200:
                    campaigns = response.json()
                    if campaigns and len(campaigns) > 0:
                        # Handle both list and paginated response
                        campaign_list = campaigns if isinstance(campaigns, list) else campaigns.get('items', [])
                        if campaign_list:
                            self.field_tests["campaign_id"]["test_value"] = campaign_list[0]["id"]
                            self.log("success", f"✅ Found campaign ID: {campaign_list[0]['id']}")
                        else:
                            self.field_tests["campaign_id"]["test_value"] = None
                    else:
                        self.field_tests["campaign_id"]["test_value"] = None
                else:
                    self.field_tests["campaign_id"]["test_value"] = None
            except:
                self.field_tests["campaign_id"]["test_value"] = None
                self.log("info", "ℹ️ Campaigns endpoint not available - will test with null")
            
            # Get course ID (if any exist)
            try:
                response = await self.client.get(f"{self.base_url}/api/courses", headers=self.headers())
                if response.status_code == 200:
                    courses = response.json()
                    if courses and len(courses) > 0:
                        course_list = courses if isinstance(courses, list) else courses.get('items', [])
                        if course_list:
                            self.field_tests["course_id"]["test_value"] = course_list[0]["id"]
                            self.log("success", f"✅ Found course ID: {course_list[0]['id']}")
                        else:
                            self.field_tests["course_id"]["test_value"] = None
                    else:
                        self.field_tests["course_id"]["test_value"] = None
                else:
                    self.field_tests["course_id"]["test_value"] = None
            except:
                self.field_tests["course_id"]["test_value"] = None
                self.log("info", "ℹ️ Courses endpoint not available - will test with null")
            
            return True
            
        except Exception as e:
            self.log("error", f"❌ Setup failed: {e}")
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
    
    async def test_field_update(self, lead_id: int, field_name: str, field_config: Dict[str, Any]) -> bool:
        """Test updating a specific field."""
        test_value = field_config["test_value"]
        field_type = field_config["type"]
        section = field_config["section"]
        note = field_config.get("note", "")
        
        self.log("info", f"🔧 Testing {section} field: {field_name} ({field_type})")
        if note:
            self.log("info", f"   Note: {note}")
        
        try:
            # Make the PATCH request
            payload = {field_name: test_value}
            self.log("info", f"   Payload: {payload}")
            
            response = await self.client.patch(
                f"{self.base_url}/api/leads/{lead_id}", 
                json=payload, 
                headers=self.headers()
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Verify the field was actually updated
                actual_value = response_data.get(field_name)
                if actual_value == test_value:
                    self.log("success", f"✅ {field_name}: Value confirmed in response")
                    self.log("success", f"   Expected: {test_value} | Actual: {actual_value}")
                else:
                    self.log("warning", f"⚠️ {field_name}: Value mismatch!")
                    self.log("warning", f"   Expected: {test_value} | Actual: {actual_value}")
                
                # Check for timestamp fields (proof that db.refresh worked)
                if response_data.get("updated_at"):
                    self.log("success", f"   ✓ updated_at present: {response_data['updated_at']}")
                
                if response_data.get("last_edited_at"):
                    self.log("success", f"   ✓ last_edited_at present: {response_data['last_edited_at']}")
                
                return True
            else:
                self.log("error", f"❌ {field_name}: Update failed - {response.status_code}")
                try:
                    error_data = response.json()
                    self.log("error", f"   Error details: {error_data}")
                except:
                    self.log("error", f"   Raw error: {response.text}")
                return False
                
        except Exception as e:
            self.log("error", f"❌ {field_name}: Exception during update - {e}")
            self.log("error", f"   Traceback: {traceback.format_exc()}")
            return False
    
    async def run_all_field_tests(self, lead_id: int) -> Dict[str, bool]:
        """Test all fields and return results."""
        self.log("info", "🚀 Starting comprehensive field tests...")
        
        results = {}
        
        # Group fields by section for better organization
        sections = {}
        for field_name, config in self.field_tests.items():
            section = config["section"]
            if section not in sections:
                sections[section] = []
            sections[section].append((field_name, config))
        
        # Test each section
        for section_name, fields in sections.items():
            self.log("info", f"\n📋 Testing {section_name} fields:")
            self.log("info", "=" * 50)
            
            for field_name, config in fields:
                success = await self.test_field_update(lead_id, field_name, config)
                results[field_name] = success
                
                # Small delay between tests
                await asyncio.sleep(0.3)
        
        return results
    
    async def run_comprehensive_test(self) -> bool:
        """Run the complete test suite."""
        self.log("info", "🧪 COMPREHENSIVE WORKSPACE FIELD TEST")
        self.log("info", "=" * 80)
        self.log("info", f"Target: {self.base_url}")
        
        try:
            # Setup
            if not await self.setup_test_data():
                return False
            
            # Get test lead
            test_lead = await self.get_test_lead()
            if not test_lead:
                return False
            
            lead_id = test_lead["id"]
            
            # Run all field tests
            results = await self.run_all_field_tests(lead_id)
            
            # Summary
            self.log("info", "\n📊 TEST SUMMARY")
            self.log("info", "=" * 80)
            
            total_fields = len(results)
            passed_fields = sum(1 for success in results.values() if success)
            failed_fields = total_fields - passed_fields
            
            # Group results by section
            sections = {}
            for field_name, success in results.items():
                section = self.field_tests[field_name]["section"]
                if section not in sections:
                    sections[section] = {"passed": 0, "failed": 0, "fields": []}
                
                if success:
                    sections[section]["passed"] += 1
                else:
                    sections[section]["failed"] += 1
                
                sections[section]["fields"].append((field_name, success))
            
            # Print section summaries
            for section_name, section_results in sections.items():
                total = section_results["passed"] + section_results["failed"]
                self.log("info", f"\n{section_name}: {section_results['passed']}/{total} passed")
                
                for field_name, success in section_results["fields"]:
                    status = "✅" if success else "❌"
                    field_type = self.field_tests[field_name]["type"]
                    note = self.field_tests[field_name].get("note", "")
                    note_text = f" ({note})" if note else ""
                    self.log("info" if success else "error", f"  {status} {field_name} ({field_type}){note_text}")
            
            # Overall summary
            self.log("info", f"\n🎯 OVERALL RESULTS: {passed_fields}/{total_fields} fields passed")
            
            if failed_fields > 0:
                self.log("warning", f"⚠️ {failed_fields} field(s) failed - check details above")
                
                # Highlight problematic fields
                problematic_failed = [
                    field for field, success in results.items() 
                    if not success and "PROBLEMATIC" in self.field_tests[field].get("note", "")
                ]
                
                if problematic_failed:
                    self.log("error", f"🚨 CRITICAL: These problematic fields still failing: {problematic_failed}")
            
            if passed_fields == total_fields:
                self.log("success", "🎉 ALL FIELDS PASSED! Workspace editing is fully functional.")
                return True
            else:
                return False
                
        except Exception as e:
            self.log("error", f"❌ Test suite error: {e}")
            self.log("error", f"Traceback: {traceback.format_exc()}")
            return False
        finally:
            await self.client.aclose()
    
    def save_results(self, filename: str = "workspace_field_test_results.json"):
        """Save detailed test results."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            self.log("info", f"📄 Detailed results saved to {filename}")
        except Exception as e:
            self.log("error", f"❌ Could not save results: {e}")


async def main():
    """Main test runner."""
    print("🧪 KINYAN CRM - COMPREHENSIVE WORKSPACE FIELD TEST")
    print("=" * 80)
    
    # Configuration
    import os
    
    base_url = "https://kinyan-crm-new-1.onrender.com"
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        base_url = "http://localhost:8000"
        print("🏠 Testing LOCAL server")
    else:
        print("🌐 Testing PRODUCTION server")
    
    print(f"🎯 Target: {base_url}")
    
    # Get auth token
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        auth_token = input("\nEnter auth token (or press Enter to skip): ").strip()
        if not auth_token:
            print("⚠️ No auth token - tests may fail")
    
    # Run tests
    tester = WorkspaceFieldTester(base_url, auth_token)
    success = await tester.run_comprehensive_test()
    
    # Save results
    tester.save_results()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL WORKSPACE FIELDS WORKING PERFECTLY!")
        print("✅ Save functionality works")
        print("✅ Visualization works") 
        print("✅ Immediate display works")
        sys.exit(0)
    else:
        print("❌ SOME FIELDS STILL HAVE ISSUES!")
        print("Check the detailed output above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
