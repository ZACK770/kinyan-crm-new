"""Test API with detailed error handling"""
import requests
import json
from datetime import datetime, timedelta

def test_create_task():
    base_url = "http://localhost:8000"
    
    # Try to find a lead first
    try:
        leads_resp = requests.get(f"{base_url}/api/leads?limit=1")
        if leads_resp.status_code != 200:
            print(f"Error fetching leads: {leads_resp.status_code}")
            return
        
        leads = leads_resp.json()
        if not leads:
            print("No leads found to attach task to")
            return
        
        lead_id = leads[0]['id']
        print(f"Found lead ID: {lead_id}")
        
        # Test task creation with full headers
        payload = {
            "lead_id": lead_id,
            "title": "Test Task from Debug Script",
            "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "task_type": "sales"
        }
        
        print(f"Sending payload: {json.dumps(payload, indent=2)}")
        
        resp = requests.post(
            f"{base_url}/api/tasks/",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer fake_token_for_dev"
            }
        )
        
        print(f"Status: {resp.status_code}")
        print(f"Headers: {dict(resp.headers)}")
        try:
            print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
        except:
            print(f"Raw Response: {resp.text}")
            
    except Exception as e:
        print(f"Connection error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_create_task()
