"""
Test R2 connection and permissions
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def test_r2():
    """Test R2 connection step by step"""
    
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME", "crm-files")
    
    print("🔍 בדיקת משתני סביבה...")
    print(f"   Account ID: {account_id}")
    print(f"   Access Key: {access_key[:10]}..." if access_key else "   Access Key: None")
    print(f"   Secret Key: {secret_key[:10]}..." if secret_key else "   Secret Key: None")
    print(f"   Bucket: {bucket_name}")
    
    if not all([account_id, access_key, secret_key]):
        print("❌ חסרים משתני סביבה")
        return
    
    print("\n🔌 יוצר חיבור ל-R2...")
    
    # Try different configurations
    configs = [
        {
            'name': 'Config 1: s3v4 + path addressing',
            'config': Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )
        },
        {
            'name': 'Config 2: s3v4 only',
            'config': Config(signature_version='s3v4')
        },
        {
            'name': 'Config 3: virtual addressing',
            'config': Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'}
            )
        },
    ]
    
    for cfg in configs:
        print(f"\n{'='*60}")
        print(f"נסיון: {cfg['name']}")
        print('='*60)
        
        try:
            client = boto3.client(
                's3',
                endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=cfg['config']
            )
            
            # Test 1: List buckets
            print("📋 בדיקה 1: רשימת buckets...")
            try:
                response = client.list_buckets()
                print(f"   ✅ מצאתי {len(response['Buckets'])} buckets:")
                for bucket in response['Buckets']:
                    print(f"      • {bucket['Name']}")
            except Exception as e:
                print(f"   ❌ שגיאה: {e}")
            
            # Test 2: Check if bucket exists
            print(f"\n📦 בדיקה 2: האם bucket '{bucket_name}' קיים?")
            try:
                client.head_bucket(Bucket=bucket_name)
                print(f"   ✅ Bucket קיים")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"   ❌ שגיאה {error_code}: {e}")
            
            # Test 3: List objects in bucket
            print(f"\n📂 בדיקה 3: רשימת קבצים ב-bucket...")
            try:
                response = client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
                if 'Contents' in response:
                    print(f"   ✅ מצאתי {len(response['Contents'])} קבצים (מתוך {response.get('KeyCount', 0)}):")
                    for obj in response['Contents'][:5]:
                        print(f"      • {obj['Key']} ({obj['Size']} bytes)")
                else:
                    print(f"   ✅ Bucket ריק")
            except Exception as e:
                print(f"   ❌ שגיאה: {e}")
            
            # Test 4: Try to upload a small test file
            print(f"\n📤 בדיקה 4: העלאת קובץ טסט...")
            try:
                test_content = b"Test file from Kinyan CRM"
                test_key = "test/connection_test.txt"
                
                client.put_object(
                    Bucket=bucket_name,
                    Key=test_key,
                    Body=test_content,
                    ContentType='text/plain'
                )
                print(f"   ✅ קובץ הועלה בהצלחה: {test_key}")
                
                # Try to read it back
                response = client.get_object(Bucket=bucket_name, Key=test_key)
                content = response['Body'].read()
                print(f"   ✅ קובץ נקרא בהצלחה: {len(content)} bytes")
                
                # Clean up
                client.delete_object(Bucket=bucket_name, Key=test_key)
                print(f"   ✅ קובץ נמחק בהצלחה")
                
                print(f"\n🎉 הקונפיגורציה הזו עובדת!")
                return
                
            except Exception as e:
                print(f"   ❌ שגיאה בהעלאה: {e}")
                import traceback
                traceback.print_exc()
        
        except Exception as e:
            print(f"❌ שגיאה ביצירת client: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_r2()
