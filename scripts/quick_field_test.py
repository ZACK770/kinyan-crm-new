#!/usr/bin/env python3
"""
Quick test for the problematic workspace fields without auth.
Tests: status, salesperson_id, course_id, source_type, campaign_id

Usage: python scripts/quick_field_test.py [lead_id]
"""

import asyncio
import sys
from datetime import datetime
import httpx
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def test_field_update(base_url: str, lead_id: int, field: str, value, description: str):
    """Test updating a single field."""
    print(f"\n🔧 Testing {description}")
    print(f"   Field: {field} = {value}")
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
        try:
            # Make PATCH request
            payload = {field: value}
            response = await client.patch(
                f"{base_url}/api/leads/{lead_id}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                actual_value = data.get(field)
                
                if actual_value == value:
                    print(f"   ✅ SUCCESS: {field} updated correctly")
                    print(f"   📊 Value: {actual_value}")
                    
                    # Check timestamps (proof db.refresh worked)
                    if data.get("updated_at"):
                        print(f"   ✓ updated_at: {data['updated_at']}")
                    if data.get("last_edited_at"):
                        print(f"   ✓ last_edited_at: {data['last_edited_at']}")
                    
                    return True
                else:
                    print(f"   ⚠️ VALUE MISMATCH: expected {value}, got {actual_value}")
                    return False
            else:
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            return False

async def main():
    """Main test runner."""
    print("🧪 QUICK WORKSPACE FIELD TEST")
    print("=" * 50)
    
    # Configuration
    base_url = "https://kinyan-crm-new-1.onrender.com"
    
    # Get lead ID
    if len(sys.argv) > 1:
        try:
            lead_id = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid lead ID. Usage: python scripts/quick_field_test.py [lead_id]")
            sys.exit(1)
    else:
        try:
            lead_id = int(input("Enter lead ID to test: "))
        except ValueError:
            print("❌ Invalid lead ID")
            sys.exit(1)
    
    print(f"🎯 Target: {base_url}")
    print(f"🔍 Testing lead ID: {lead_id}")
    
    # Test the problematic fields
    timestamp = datetime.now().strftime("%H%M%S")
    
    tests = [
        # (field, value, description)
        ("status", "ליד בתהליך", "Status field (select)"),
        ("salesperson_id", 1, "Salesperson field (entity-select)"),
        ("source_type", "elementor", "Source type field (select)"),
        ("campaign_id", 1, "Campaign field (entity-select)"),
        ("course_id", 1, "Course field (entity-select)"),
        ("notes", f"Quick test {timestamp}", "Notes field (text)"),
        ("id_number", "987654321", "ID Number (original 500 cause)"),
    ]
    
    results = []
    
    for field, value, description in tests:
        success = await test_field_update(base_url, lead_id, field, value, description)
        results.append((field, success, description))
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    passed = 0
    failed = 0
    
    for field, success, description in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {field} - {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n🎯 SUMMARY: {passed}/{len(results)} tests passed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Workspace fields are working correctly.")
    else:
        print(f"⚠️ {failed} test(s) failed. Check the output above for details.")
        
        # Highlight the problematic ones
        problematic = ["status", "salesperson_id", "course_id", "source_type", "campaign_id"]
        failed_problematic = [field for field, success, _ in results if not success and field in problematic]
        
        if failed_problematic:
            print(f"🚨 CRITICAL: These problematic fields still failing: {failed_problematic}")

if __name__ == "__main__":
    asyncio.run(main())
