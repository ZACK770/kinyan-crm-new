"""
Debug R2 connection with detailed logging
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.config import Config
import logging

# Enable debug logging
boto3.set_stream_logger('boto3.resources', logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

account_id = os.getenv("R2_ACCOUNT_ID")
access_key = os.getenv("R2_ACCESS_KEY_ID")
secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("R2_BUCKET_NAME", "crm-files")

print("="*60)
print("R2 Configuration:")
print("="*60)
print(f"Account ID: {account_id}")
print(f"Access Key: {access_key}")
print(f"Secret Key: {secret_key[:20]}...{secret_key[-10:]}")
print(f"Bucket: {bucket_name}")
print(f"Endpoint: https://{account_id}.r2.cloudflarestorage.com")
print("="*60)

print("\nCreating S3 client...")
client = boto3.client(
    's3',
    endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
)

print("\nTrying to list buckets...")
try:
    response = client.list_buckets()
    print(f"Success! Found {len(response['Buckets'])} buckets")
    for bucket in response['Buckets']:
        print(f"  - {bucket['Name']}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
