"""
Quick R2 credentials verification
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.config import Config
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("R2_BUCKET_NAME", "crm-files")
verify_ssl = os.getenv("R2_VERIFY_SSL", "true").lower() != "false"

# Jurisdiction-specific endpoint
jurisdiction = os.getenv("R2_JURISDICTION", "").lower()
if jurisdiction:
    endpoint_url = f'https://{account_id}.{jurisdiction}.r2.cloudflarestorage.com'
else:
    endpoint_url = f'https://{account_id}.r2.cloudflarestorage.com'

print("="*60)
print("🔍 R2 Credentials Verification")
print("="*60)
print(f"Account ID: {account_id}")
print(f"Access Key length: {len(access_key) if access_key else 0} chars")
print(f"Secret Key length: {len(secret_key) if secret_key else 0} chars")
print(f"Bucket: {bucket_name}")
print(f"Jurisdiction: {jurisdiction if jurisdiction else 'default'}")
print(f"Endpoint: {endpoint_url}")
print(f"SSL Verify: {verify_ssl}")
print("="*60)

# Check credential format
print("\n📋 Credential Format Check:")
if access_key and len(access_key) < 20:
    print("   ⚠️  Access Key נראה קצר מדי!")
    print("   💡 R2 Access Keys בדרך כלל 20+ תווים")
else:
    print("   ✅ Access Key length OK")

if secret_key and len(secret_key) < 40:
    print("   ⚠️  Secret Key נראה קצר מדי!")
    print("   💡 R2 Secret Keys בדרך כלל 40+ תווים")
else:
    print("   ✅ Secret Key length OK")

# Try to connect
print("\n🔌 Testing Connection...")
try:
    client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        ),
        verify=verify_ssl
    )
    
    # Test list buckets
    print("   Testing: list_buckets()...")
    response = client.list_buckets()
    print(f"   ✅ SUCCESS! Found {len(response['Buckets'])} buckets:")
    for bucket in response['Buckets']:
        print(f"      • {bucket['Name']}")
    
    # Test bucket access
    print(f"\n   Testing: head_bucket('{bucket_name}')...")
    client.head_bucket(Bucket=bucket_name)
    print(f"   ✅ Bucket '{bucket_name}' accessible!")
    
    # Test upload
    print(f"\n   Testing: upload small file...")
    test_key = "test/verify_test.txt"
    client.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=b"Test from verification script",
        ContentType='text/plain'
    )
    print(f"   ✅ Upload successful!")
    
    # Clean up
    client.delete_object(Bucket=bucket_name, Key=test_key)
    print(f"   ✅ Cleanup successful!")
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("="*60)
    print("✅ R2 credentials are valid and working")
    print("✅ You can upload files to R2")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    print("\n" + "="*60)
    print("❌ CREDENTIALS ARE INVALID")
    print("="*60)
    print("\n💡 Solution:")
    print("1. Go to Cloudflare Dashboard → R2")
    print("2. Click 'Manage R2 API Tokens' (NOT regular API Tokens!)")
    print("3. Create API Token with 'Object Read & Write' permissions")
    print("4. Copy the Access Key ID and Secret Access Key")
    print("5. Update your .env file with the new credentials")
    print("\n⚠️  Make sure you're creating R2 API Tokens, not Cloudflare API Tokens!")
    sys.exit(1)
