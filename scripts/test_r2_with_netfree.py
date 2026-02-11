"""
Test R2 with NetFree SSL bypass
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.config import Config
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("R2_BUCKET_NAME", "crm-files")

print("="*60)
print("🔍 בדיקת R2 עם NetFree bypass")
print("="*60)
print(f"Account ID: {account_id}")
print(f"Access Key: {access_key}")
print(f"Secret Key: {secret_key[:20]}...{secret_key[-10:]}")
print(f"Bucket: {bucket_name}")
print("="*60)

# Create client with SSL verification disabled
print("\n📡 יוצר S3 client עם verify=False...")
client = boto3.client(
    's3',
    endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    ),
    verify=False
)

# Test 1: List buckets
print("\n1️⃣ בדיקה: List Buckets...")
try:
    response = client.list_buckets()
    print(f"   ✅ הצליח! מצאתי {len(response['Buckets'])} buckets:")
    for bucket in response['Buckets']:
        print(f"      • {bucket['Name']}")
except Exception as e:
    print(f"   ❌ נכשל: {e}")
    print(f"\n   💡 אם זה נכשל, הבעיה היא ב-credentials (Access Key/Secret Key)")
    print(f"      בדוק ב-Cloudflare Dashboard → R2 → Manage R2 API Tokens")
    sys.exit(1)

# Test 2: Check bucket exists
print(f"\n2️⃣ בדיקה: האם bucket '{bucket_name}' קיים?")
try:
    client.head_bucket(Bucket=bucket_name)
    print(f"   ✅ Bucket קיים!")
except Exception as e:
    print(f"   ❌ נכשל: {e}")
    print(f"      הבעיה: Bucket '{bucket_name}' לא קיים או אין הרשאות")
    sys.exit(1)

# Test 3: Upload test file
print(f"\n3️⃣ בדיקה: העלאת קובץ טסט...")
try:
    test_content = b"Test from Kinyan CRM - NetFree compatible!"
    test_key = "test/netfree_test.txt"
    
    client.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=test_content,
        ContentType='text/plain'
    )
    print(f"   ✅ קובץ הועלה: {test_key}")
    
    # Read it back
    response = client.get_object(Bucket=bucket_name, Key=test_key)
    content = response['Body'].read()
    print(f"   ✅ קובץ נקרא: {len(content)} bytes")
    
    # Delete it
    client.delete_object(Bucket=bucket_name, Key=test_key)
    print(f"   ✅ קובץ נמחק")
    
except Exception as e:
    print(f"   ❌ נכשל: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("🎉 כל הבדיקות עברו בהצלחה!")
print("="*60)
print("✅ R2 עובד עם NetFree")
print("✅ ניתן להמשיך להעלות קבצים")
