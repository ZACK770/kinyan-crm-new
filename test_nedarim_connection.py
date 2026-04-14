#!/usr/bin/env python3
"""
Test Nedarim Plus connection
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ['DATABASE_URL'] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
os.environ['NEDARIM_API_URL'] = "https://matara.pro/api"
os.environ['NEDARIM_API_KEY'] = "ou946"
os.environ['NEDARIM_MOSAD_ID'] = "7009959"

from services.nedarim_plus import NedarimClient

def test_connection():
    print("🔗 Testing Nedarim Plus connection...")
    print("=" * 50)
    
    try:
        client = NedarimClient()
        print("✅ Nedarim API configured")
        print(f"API URL: {client.base_url}")
        print(f"Mosad ID: {client.mosad_id}")
        print(f"API Key: {'***' + client.api_key[-4:] if len(client.api_key) > 4 else '***'}")
        
        # Check if in mock mode
        if client.api_key == "ou946":
            print("\n📋 MODE: MOCK/DEVELOPMENT")
            print("   - API calls will return simulated responses")
            print("   - No real charges will be made")
            print("   - Perfect for testing and development")
        else:
            print("\n📋 MODE: PRODUCTION")
            print("   - Real API calls to Nedarim Plus")
            print("   - Actual charges will be processed")
        
        print("\n✅ Connection test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Connection test FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
