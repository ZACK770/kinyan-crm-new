"""
Diagnose NetFree/SSL issues with R2 connection
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.config import Config
import ssl
import socket
import httpx

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

account_id = os.getenv("R2_ACCOUNT_ID")
bucket_name = os.getenv("R2_BUCKET_NAME", "crm-files")

print("="*60)
print("🔍 בדיקת חיבור ל-Cloudflare R2 (NetFree Diagnostics)")
print("="*60)

# Test 1: DNS Resolution
print("\n1️⃣ בדיקת DNS Resolution...")
endpoint = f"{account_id}.r2.cloudflarestorage.com"
try:
    ip = socket.gethostbyname(endpoint)
    print(f"   ✅ DNS עובד: {endpoint} -> {ip}")
except Exception as e:
    print(f"   ❌ DNS נכשל: {e}")

# Test 2: TCP Connection
print("\n2️⃣ בדיקת TCP Connection על פורט 443...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((endpoint, 443))
    sock.close()
    if result == 0:
        print(f"   ✅ TCP Connection הצליח")
    else:
        print(f"   ❌ TCP Connection נכשל (error code: {result})")
except Exception as e:
    print(f"   ❌ TCP Connection נכשל: {e}")

# Test 3: SSL Certificate
print("\n3️⃣ בדיקת SSL Certificate...")
try:
    context = ssl.create_default_context()
    with socket.create_connection((endpoint, 443), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=endpoint) as ssock:
            cert = ssock.getpeercert()
            print(f"   ✅ SSL Certificate תקין")
            print(f"      Subject: {dict(x[0] for x in cert['subject'])}")
            print(f"      Issuer: {dict(x[0] for x in cert['issuer'])}")
            print(f"      Valid until: {cert['notAfter']}")
except ssl.SSLError as e:
    print(f"   ⚠️  SSL Error: {e}")
    print(f"      זה יכול להיות NetFree/SSL Inspection!")
except Exception as e:
    print(f"   ❌ SSL נכשל: {e}")

# Test 4: SSL Certificate with verification disabled
print("\n4️⃣ בדיקת חיבור ללא אימות SSL (NetFree bypass)...")
try:
    context = ssl._create_unverified_context()
    with socket.create_connection((endpoint, 443), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=endpoint) as ssock:
            cert = ssock.getpeercert()
            print(f"   ✅ חיבור ללא אימות הצליח")
            if cert:
                issuer = dict(x[0] for x in cert['issuer'])
                print(f"      Issuer: {issuer}")
                if 'NetFree' in str(issuer) or 'Rimon' in str(issuer):
                    print(f"      🔍 זוהה NetFree/Rimon Certificate!")
except Exception as e:
    print(f"   ❌ נכשל: {e}")

# Test 5: HTTP Request with httpx library
print("\n5️⃣ בדיקת HTTP Request עם httpx...")
try:
    url = f"https://{endpoint}"
    response = httpx.get(url, timeout=5)
    print(f"   ✅ HTTP Request הצליח: {response.status_code}")
except httpx.ConnectError as e:
    print(f"   ⚠️  SSL Error: {e}")
    print(f"      זה כנראה NetFree SSL Inspection!")
except Exception as e:
    print(f"   ❌ נכשל: {e}")

# Test 6: Try boto3 with SSL verification disabled
print("\n6️⃣ בדיקת boto3 ללא אימות SSL...")
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    client = boto3.client(
        's3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        ),
        verify=False  # Disable SSL verification
    )
    
    response = client.list_buckets()
    print(f"   ✅ boto3 ללא SSL verification עבד!")
    print(f"      מצאתי {len(response['Buckets'])} buckets:")
    for bucket in response['Buckets']:
        print(f"         • {bucket['Name']}")
except Exception as e:
    print(f"   ❌ נכשל: {e}")

print("\n" + "="*60)
print("📊 סיכום:")
print("="*60)
print("""
אם בדיקה 3 (SSL Certificate) נכשלה אבל בדיקה 6 (ללא SSL verification) הצליחה,
אז הבעיה היא NetFree SSL Inspection.

פתרונות אפשריים:
1. הוסף את *.r2.cloudflarestorage.com לרשימת החריגים של NetFree
2. השתמש ב-verify=False בקוד (לא מומלץ לפרודקשן)
3. התקן את תעודת NetFree Root CA במערכת
4. השתמש ב-Custom Domain עם R2 שעובר דרך Cloudflare Workers
""")
