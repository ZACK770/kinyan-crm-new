import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test file metadata endpoint
print("Testing file metadata endpoint...")
response = requests.get("https://kinyan-crm-new-1.onrender.com/api/files/76", verify=False)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"File data: {data}")
else:
    print(f"Error: {response.text}")

# Test download endpoint
print("\nTesting download endpoint...")
response = requests.get("https://kinyan-crm-new-1.onrender.com/api/files/76/download", allow_redirects=False, verify=False)
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
if response.status_code >= 400:
    print(f"Error: {response.text}")
