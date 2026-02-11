"""Test the actual API upload endpoint"""
import httpx

url = "http://localhost:8005/api/files/upload"
params = {"entity_type": "temp", "entity_id": 0}
files = {"file": ("test.txt", b"Hello World", "text/plain")}

r = httpx.post(url, params=params, files=files)
print(f"Status: {r.status_code}")
print(f"Body: {r.text}")
