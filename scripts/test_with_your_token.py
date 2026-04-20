#!/usr/bin/env python3
"""
Test problematic workspace fields with YOUR auth token.
Just paste your token when prompted and it will test everything.
"""

import asyncio
import sys
from datetime import datetime
import httpx
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def test_field_update(base_url: str, lead_id: int, field: str, value, description: str, auth_token: str):
    """Test updating a single field."""
    print(f"\n🔧 Testing {description}")
    print(f"   Field: {field} = {value}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
        try:
            payload = {field: value}
            
            response = await client.patch(
                f"{base_url}/api/leads/{lead_id}",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                actual_value = data.get(field)
                
                # Check if value matches
                if field.endswith("_id") and value is not None:
                    success = actual_value is not None and int(actual_value) == int(value)
                else:
                    success = actual_value == value
                
                if success:
                    print(f"   ✅ SUCCESS: {field} = {actual_value}")
                    if data.get("updated_at"):
                        print(f"   ✓ updated_at: {data['updated_at']}")
                    if data.get("last_edited_at"):
                        print(f"   ✓ last_edited_at: {data['last_edited_at']}")
                    return True
                else:
                    print(f"   ⚠️ MISMATCH: expected {value}, got {actual_value}")
                    return False
            else:
                print(f"   ❌ FAILED: HTTP {response.status_code}")
                if response.status_code == 401:
                    print(f"   Token may be expired or invalid")
                else:
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Raw: {response.text[:100]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            return False

async def get_lead_id(base_url: str, auth_token: str) -> int:
    """Get a valid lead ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
        try:
            response = await client.get(f"{base_url}/api/leads?limit=1", headers=headers)
            if response.status_code == 200:
                leads = response.json()
                if leads:
                    lead = leads[0]
                    print(f"✅ Found lead: {lead['full_name']} (ID: {lead['id']})")
                    return lead['id']
        except:
            pass
    
    print("⚠️ Using default lead ID: 1")
    return 1

async def main():
    print("🧪 WORKSPACE FIELDS TEST WITH YOUR TOKEN")
    print("=" * 50)
    
    base_url = "https://kinyan-crm-new-1.onrender.com"
    print(f"🎯 Target: {base_url}")
    
    # Get YOUR auth token
    print("\n🔑 I need your auth token to test the fixes.")
    print("To get it:")
    print("1. Go to https://kinyan-crm-new-1.onrender.com")
    print("2. Login normally")
    print("3. Press F12 (dev tools)")
    print("4. Go to Application → Local Storage → kinyan-crm-new-1.onrender.com")
    print("5. Copy the 'auth_token' value")
    print()
    
    auth_token = input("Paste your auth token here: ").strip()
    if not auth_token:
        print("❌ No token provided - cannot test")
        sys.exit(1)
    
    # Get lead ID
    lead_id = await get_lead_id(base_url, auth_token)
    print(f"🎯 Testing lead ID: {lead_id}")
    
    # Test the 5 problematic fields
    timestamp = datetime.now().strftime("%H%M%S")
    
    tests = [
        ("status", "ליד בתהליך", "🚨 Status field (select)"),
        ("salesperson_id", 1, "🚨 Salesperson field (entity-select)"),
        ("course_id", 1, "🚨 Course field (entity-select)"),
        ("source_type", "elementor", "🚨 Source type field (select)"),
        ("campaign_id", 1, "🚨 Campaign field (entity-select)"),
        ("notes", f"Test {timestamp}", "✅ Notes (for comparison)"),
        ("id_number", "123456789", "✅ ID Number (was 500 cause)"),
    ]
    
    results = []
    for field, value, description in tests:
        success = await test_field_update(base_url, lead_id, field, value, description, auth_token)
        results.append((field, success))
        await asyncio.sleep(0.2)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS:")
    
    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    problematic_fields = ["status", "salesperson_id", "course_id", "source_type", "campaign_id"]
    problematic_results = [(field, success) for field, success in results if field in problematic_fields]
    problematic_passed = sum(1 for _, success in problematic_results if success)
    
    for field, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        marker = "🚨" if field in problematic_fields else "  "
        print(f"   {marker} {status} {field}")
    
    print(f"\n🎯 OVERALL: {passed}/{len(results)} passed")
    print(f"🚨 PROBLEMATIC: {problematic_passed}/{len(problematic_fields)} working")
    
    if problematic_passed == len(problematic_fields):
        print("\n🎉 ALL PROBLEMATIC FIELDS ARE NOW WORKING!")
        print("✅ The fixes are successful!")
    else:
        failed_problematic = [field for field, success in problematic_results if not success]
        print(f"\n⚠️ Still failing: {failed_problematic}")

if __name__ == "__main__":
    asyncio.run(main())
