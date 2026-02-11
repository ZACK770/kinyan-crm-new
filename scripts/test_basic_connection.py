"""
Test basic network connectivity to R2
"""
import socket
import ssl

account_id = "da53b4cd888030bba791621ea1a39f8c"
endpoints = [
    f"{account_id}.r2.cloudflarestorage.com",
    f"{account_id}.eu.r2.cloudflarestorage.com"
]

for endpoint in endpoints:
    print("="*60)
    print(f"Testing: {endpoint}")
    print("="*60)
    
    # DNS Resolution
    try:
        ip = socket.gethostbyname(endpoint)
        print(f"✅ DNS: {ip}")
    except Exception as e:
        print(f"❌ DNS failed: {e}")
        continue
    
    # TCP Connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((endpoint, 443))
        print(f"✅ TCP connection successful")
        sock.close()
    except Exception as e:
        print(f"❌ TCP failed: {e}")
        continue
    
    # SSL Handshake
    try:
        context = ssl._create_unverified_context()
        with socket.create_connection((endpoint, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=endpoint) as ssock:
                cert = ssock.getpeercert()
                if cert:
                    issuer = dict(x[0] for x in cert['issuer'])
                    print(f"✅ SSL handshake successful")
                    print(f"   Issuer: {issuer.get('organizationName', 'Unknown')}")
                    if 'NetFree' in str(issuer) or 'Rimon' in str(issuer):
                        print(f"   ⚠️  NetFree certificate detected!")
    except Exception as e:
        print(f"❌ SSL failed: {e}")
    
    print()

print("\n" + "="*60)
print("💡 Diagnosis:")
print("="*60)
print("If DNS and TCP work but boto3 fails, the issue is likely:")
print("1. NetFree is intercepting/blocking S3 API calls")
print("2. The credentials format is incorrect")
print("3. R2 API endpoint requires specific headers that NetFree blocks")
print("\nTry uploading from Render (without NetFree) to confirm.")
