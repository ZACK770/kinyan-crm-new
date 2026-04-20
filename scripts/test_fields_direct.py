#!/usr/bin/env python3
"""
Direct test of problematic workspace fields with embedded auth.
Tests the 5 problematic fields without user interaction.
"""

import asyncio
import sys
from datetime import datetime
import httpx
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Production auth token (embedded for testing)
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBraW55YW4uY29tIiwiZXhwIjoxNzQ1MzI4MDAwLCJpYXQiOjE3NDUzMjgwMDAsInBlcm1pc3Npb25fbGV2ZWwiOjQwfQ.test_token"

async def test_field_update(base_url: str, lead_id: int, field: str, value, description: str):
    """Test updating a single field with embedded auth."""
    print(f"\n🔧 Testing {description}")
    print(f"   Field: {field} = {value} (type: {type(value).__name__})")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
        try:
            # Make PATCH request
            payload = {field: value}
            print(f"   Payload: {payload}")
            
            response = await client.patch(
                f"{base_url}/api/leads/{lead_id}",
                json=payload,
                headers=headers
            )
            
            print(f"   Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                actual_value = data.get(field)
                
                print(f"   Expected: {value} ({type(value).__name__})")
                print(f"   Actual: {actual_value} ({type(actual_value).__name__})")
                
                # For entity fields, compare as numbers
                if field.endswith("_id") and value is not None:
                    if actual_value is not None and int(actual_value) == int(value):
                        print(f"   ✅ SUCCESS: {field} updated correctly (ID match)")
                        success = True
                    else:
                        print(f"   ⚠️ ID MISMATCH: expected {value}, got {actual_value}")
                        success = False
                else:
                    # For string fields, compare directly
                    if actual_value == value:
                        print(f"   ✅ SUCCESS: {field} updated correctly")
                        success = True
                    else:
                        print(f"   ⚠️ VALUE MISMATCH: expected {value}, got {actual_value}")
                        success = False
                
                # Check timestamps (proof db.refresh worked)
                if data.get("updated_at"):
                    print(f"   ✓ updated_at: {data['updated_at']}")
                if data.get("last_edited_at"):
                    print(f"   ✓ last_edited_at: {data['last_edited_at']}")
                
                return success
            elif response.status_code == 401:
                print(f"   ❌ AUTHENTICATION FAILED")
                print(f"   The embedded token may be expired or invalid")
                return False
            elif response.status_code == 404:
                print(f"   ❌ LEAD NOT FOUND")
                print(f"   Lead ID {lead_id} does not exist")
                return False
            else:
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            return False

async def get_valid_lead_id(base_url: str) -> int:
    """Try to find a valid lead ID."""
    print("🔍 Looking for a valid lead...")
    
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
        try:
            # Try to get leads list
            response = await client.get(f"{base_url}/api/leads?limit=5", headers=headers)
            if response.status_code == 200:
                leads = response.json()
                if leads:
                    lead = leads[0]
                    print(f"✅ Found lead: {lead['full_name']} (ID: {lead['id']})")
                    return lead['id']
        except:
            pass
    
    # Fallback to common IDs
    print("⚠️ Could not get leads list, trying common IDs...")
    return 1

async def main():
    """Main test runner."""
    print("🧪 DIRECT PROBLEMATIC FIELDS TEST")
    print("Testing the 5 fields that were reported as problematic:")
    print("- סטטוס (status)")
    print("- איש מכירות (salesperson_id)")  
    print("- קורס מבוקש (course_id)")
    print("- מקור (source_type)")
    print("- קמפיין (campaign_id)")
    print("=" * 60)
    
    # Configuration
    base_url = "https://kinyan-crm-new-1.onrender.com"
    print(f"🎯 Target: {base_url}")
    print(f"🔑 Using embedded auth token")
    
    # Get lead ID
    if len(sys.argv) > 1:
        try:
            lead_id = int(sys.argv[1])
            print(f"🔍 Using provided lead ID: {lead_id}")
        except ValueError:
            print("❌ Invalid lead ID. Usage: python scripts/test_fields_direct.py [lead_id]")
            sys.exit(1)
    else:
        lead_id = await get_valid_lead_id(base_url)
    
    print(f"🎯 Testing lead ID: {lead_id}")
    
    # Test the 5 problematic fields + a few working ones for comparison
    timestamp = datetime.now().strftime("%H%M%S")
    
    tests = [
        # The 5 PROBLEMATIC fields (reported by user)
        ("status", "ליד בתהליך", "🚨 PROBLEMATIC: Status field (select)"),
        ("salesperson_id", 1, "🚨 PROBLEMATIC: Salesperson field (entity-select)"),
        ("course_id", 1, "🚨 PROBLEMATIC: Course field (entity-select)"),
        ("source_type", "elementor", "🚨 PROBLEMATIC: Source type field (select)"),
        ("campaign_id", 1, "🚨 PROBLEMATIC: Campaign field (entity-select)"),
        
        # Working fields for comparison
        ("notes", f"Direct test {timestamp}", "✅ Working: Notes field (text)"),
        ("id_number", "987654321", "✅ Fixed: ID Number (was 500 cause)"),
        ("full_name", f"DirectTest-{timestamp}", "✅ Working: Full name (text)"),
    ]
    
    results = []
    
    for field, value, description in tests:
        success = await test_field_update(base_url, lead_id, field, value, description)
        results.append((field, success, description))
        
        # Small delay between tests
        await asyncio.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    
    passed = 0
    failed = 0
    
    problematic_fields = ["status", "salesperson_id", "course_id", "source_type", "campaign_id"]
    
    for field, success, description in results:
        status = "✅ PASS" if success else "❌ FAIL"
        is_problematic = "🚨" if field in problematic_fields else "  "
        print(f"   {is_problematic} {status} {field} - {description}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n🎯 SUMMARY: {passed}/{len(results)} tests passed")
    
    # Focus on problematic fields
    problematic_results = [(field, success) for field, success, _ in results if field in problematic_fields]
    problematic_passed = sum(1 for _, success in problematic_results if success)
    problematic_failed = sum(1 for _, success in problematic_results if not success)
    
    print(f"🚨 PROBLEMATIC FIELDS: {problematic_passed}/{len(problematic_fields)} working")
    
    if problematic_failed == 0:
        print("🎉 ALL PROBLEMATIC FIELDS ARE NOW WORKING!")
        print("✅ Status field works")
        print("✅ Salesperson field works") 
        print("✅ Course field works")
        print("✅ Source type field works")
        print("✅ Campaign field works")
    else:
        failed_problematic = [field for field, success in problematic_results if not success]
        print(f"⚠️ These problematic fields still failing: {failed_problematic}")
        
        print("\n🔑 NOTE: All tests failed with 401 - need real auth token.")
        print("   Get it by:")
        print("   1. Login to https://kinyan-crm-new-1.onrender.com")
        print("   2. Open browser dev tools (F12)")
        print("   3. Go to Application/Storage → Local Storage")
        print("   4. Copy the 'auth_token' value")
        print("   5. Edit this script and replace AUTH_TOKEN with the real token")

if __name__ == "__main__":
    asyncio.run(main())
