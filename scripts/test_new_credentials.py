"""
Test the new R2 credentials directly
"""
import boto3
from botocore.config import Config
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# New credentials from Cloudflare
account_id = "da53b4cd888030bba791621ea1a39f8c"
access_key = "da07d3d09efdf2a43d1830e88b46fea4"
secret_key = "ef498adb5581f3b9b8d7a124aa21fa79f878d94d1877a0cacafa4e70d70bea3a"
bucket_name = "crm-files"

# Test both endpoints
endpoints = [
    ("Default", f'https://{account_id}.r2.cloudflarestorage.com'),
    ("EU", f'https://{account_id}.eu.r2.cloudflarestorage.com'),
]

for name, endpoint_url in endpoints:
    print("="*60)
    print(f"Testing {name} Endpoint")
    print("="*60)
    print(f"Endpoint: {endpoint_url}")
    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key[:20]}...{secret_key[-10:]}")
    
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
            verify=False  # Disable SSL for NetFree
        )
        
        # Test list buckets
        print("\n📋 Testing list_buckets()...")
        response = client.list_buckets()
        print(f"✅ SUCCESS! Found {len(response['Buckets'])} buckets:")
        for bucket in response['Buckets']:
            print(f"   • {bucket['Name']}")
        
        # Test bucket access
        print(f"\n📦 Testing head_bucket('{bucket_name}')...")
        client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' accessible!")
        
        # Test upload
        print(f"\n📤 Testing upload...")
        test_key = "test/verify_new_creds.txt"
        client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=b"Test from new credentials",
            ContentType='text/plain'
        )
        print(f"✅ Upload successful!")
        
        # Clean up
        client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ Cleanup successful!")
        
        print("\n" + "="*60)
        print(f"🎉 {name} ENDPOINT WORKS!")
        print("="*60)
        print(f"\nUse this in your .env:")
        if name == "EU":
            print(f"R2_JURISDICTION=eu")
        else:
            print(f"# R2_JURISDICTION= (leave empty or comment out)")
        break
        
    except Exception as e:
        print(f"\n❌ {name} endpoint failed: {e}")
        print()

print("\n" + "="*60)
print("Update your .env with the working configuration above!")
print("="*60)
