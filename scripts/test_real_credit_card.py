"""
Test script with REAL credit card - HK with 3 months of 5 ILS
Testing standing order without authorization hold
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables if not set
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
if not os.getenv('NEDARIM_MOSAD_ID'):
    os.environ['NEDARIM_MOSAD_ID'] = "7009959"
if not os.getenv('NEDARIM_API_PASSWORD'):
    os.environ['NEDARIM_API_PASSWORD'] = "ou946"

from services.nedarim_debit_card import NedarimDebitCardService, NedarimDebitCardError


async def test_real_credit_card():
    """Test with real credit card - HK with 3 months of 5 ILS"""
    
    print("=" * 80)
    print("TEST: REAL CREDIT CARD - HK with 3 months")
    print("⚠️  WARNING: This will charge a REAL credit card!")
    print("=" * 80)
    
    service = NedarimDebitCardService()
    
    # REAL credit card details
    card_number = "4580170008989957"
    expiry = "0129"
    cvv = "714"
    
    # Test case - HK with 3 months of 5 ILS
    test_case = {
        "name": "HK - 3 חודשים של ₪5 (סה\"כ ₪15)",
        "payment_type": "HK",
        "monthly_amount": 5.0,
        "months": 3,
        "total_expected": 15.0,
    }
    
    print(f"\n{'─' * 80}")
    print(f"Test: {test_case['name']}")
    print(f"{'─' * 80}")
    print(f"Payment Type: {test_case['payment_type']}")
    print(f"Monthly Amount: ₪{test_case['monthly_amount']}")
    print(f"Number of Months: {test_case['months']}")
    print(f"Total Expected: ₪{test_case['total_expected']}")
    print()
    print("📋 Sending to API:")
    print(f"   PaymentType = HK")
    print(f"   Amount = ₪{test_case['monthly_amount']} (monthly)")
    print(f"   Tashloumim = {test_case['months']} (months)")
    print()
    
    try:
        result = await service.charge_card(
            client_name="Test User - Real Card",
            card_number=card_number,
            expiry=expiry,
            cvv=cvv,
            amount=test_case['monthly_amount'],  # Monthly amount: 5 ILS
            installments=test_case['months'],     # Number of months: 3
            payment_type=test_case['payment_type'],
            phone="0501234567",
            comments=f"Test {test_case['name']}",
        )
        
        print("=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Confirmation: {result.get('confirmation')}")
        print(f"Amount: ₪{result.get('amount')}")
        print(f"Installments: {result.get('installments')}")
        print(f"Card Last 4: {result.get('card_last_4')}")
        print(f"Receipt Number: {result.get('receipt_number')}")
        print(f"Transaction Time: {result.get('transaction_time')}")
        print(f"Message: {result.get('message')}")
        
        print("\n" + "=" * 80)
        print("📋 FULL RESPONSE:")
        print("=" * 80)
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 80)
        print("🎉 STANDING ORDER CREATED!")
        print("=" * 80)
        print(f"Monthly charge: ₪{test_case['monthly_amount']}")
        print(f"Number of months: {test_case['months']}")
        print(f"Total over period: ₪{test_case['total_expected']}")
        print("=" * 80)
        
    except NedarimDebitCardError as e:
        print("=" * 80)
        print("❌ FAILED!")
        print("=" * 80)
        print(f"Error Message: {e.message}")
        print(f"Error Code: {e.error_code}")
        print(f"Details: {e.details}")
        print("=" * 80)
        
    except Exception as e:
        print("=" * 80)
        print("❌ UNEXPECTED ERROR!")
        print("=" * 80)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
    
    print()


if __name__ == "__main__":
    asyncio.run(test_real_credit_card())
