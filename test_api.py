#!/usr/bin/env python3
import requests
import json

def test_exam_registration_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Exam Registration API...")
    
    # Test 1: Get upcoming exam dates
    print("\n1. Testing GET /public/exam-registration/exam-dates/upcoming")
    try:
        response = requests.get(f"{base_url}/public/exam-registration/exam-dates/upcoming")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Found {len(data)} exam dates")
            if data:
                print(f"  First date: {data[0]['date']} - {data[0]['description']}")
                print(f"  Exams: {len(data[0]['exams'])}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Connection error: {e}")
    
    # Test 2: Register for an exam
    print("\n2. Testing POST /public/exam-registration/register")
    if 'data' in locals() and data:
        exam_date_id = data[0]['exam_date_id']
        exam_id = data[0]['exams'][0]['exam_id']
        
        payload = {
            "exam_date_id": exam_date_id,
            "exam_id": exam_id,
            "phone": "0509999999",
            "name": "נבחן טסט"
        }
        
        try:
            response = requests.post(
                f"{base_url}/public/exam-registration/register",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                reg_data = response.json()
                print(f"✓ Registration successful!")
                print(f"  Registration code: {reg_data['registration_code']}")
                print(f"  Exam: {reg_data['exam_name']}")
                print(f"  Date: {reg_data['exam_date']}")
            else:
                print(f"✗ Error: {response.text}")
        except Exception as e:
            print(f"✗ Connection error: {e}")
    
    # Test 3: Get registrations by phone
    print("\n3. Testing GET /public/exam-registration/registrations/0509999999")
    try:
        response = requests.get(f"{base_url}/public/exam-registration/registrations/0509999999")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            regs = response.json()
            print(f"✓ Success! Found {len(regs)} registrations")
            for reg in regs:
                print(f"  - {reg['exam_name']} ({reg['exam_date']}) - {reg['status']}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Connection error: {e}")

if __name__ == "__main__":
    test_exam_registration_api()
