"""
Test script for HK - CORRECT according to documentation
Amount = monthly payment (not total)
Tashloumim = number of months (not installments)
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


async def test_hk_correct():
    """Test HK correctly - Amount=monthly, Tashloumim=months"""
    
    print("=" * 80)
    print("TEST: HK - CORRECT per documentation")
    print("Amount = monthly payment (NOT total)")
    print("Tashloumim = number of months to charge")
    print("=" * 80)
    
    service = NedarimDebitCardService()
    
    # Test card details (not real/active)
    card_number = "5326141204526337"
    expiry = "1030"
    cvv = "809"
    
    # Test scenarios - Amount is MONTHLY, Tashloumim is MONTHS
    test_cases = [
        {
            "name": "HK - ₪100 לחודש למשך 3 חודשים",
            "payment_type": "HK",
            "monthly_amount": 100.0,
            "months": 3,
            "total_expected": 300.0,
        },
        {
            "name": "HK - ₪100 לחודש למשך 6 חודשים",
            "payment_type": "HK",
            "monthly_amount": 100.0,
            "months": 6,
            "total_expected": 600.0,
        },
        {
            "name": "HK - ₪100 לחודש למשך 12 חודשים",
            "payment_type": "HK",
            "monthly_amount": 100.0,
            "months": 12,
            "total_expected": 1200.0,
        },
        {
            "name": "HK - ₪250 לחודש למשך 6 חודשים",
            "payment_type": "HK",
            "monthly_amount": 250.0,
            "months": 6,
            "total_expected": 1500.0,
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test Case {i}: {test_case['name']}")
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
                client_name="Test User - HK Correct",
                card_number=card_number,
                expiry=expiry,
                cvv=cvv,
                amount=test_case['monthly_amount'],  # Monthly amount
                installments=test_case['months'],     # Number of months
                payment_type=test_case['payment_type'],
                email="test@example.com",
                phone="0501234567",
                comments=f"Test {test_case['name']}",
            )
            
            print("✅ SUCCESS!")
            print(f"Transaction ID: {result.get('transaction_id')}")
            print(f"Confirmation: {result.get('confirmation')}")
            print(f"Amount: ₪{result.get('amount')}")
            print(f"Installments: {result.get('installments')}")
            print(f"Card Last 4: {result.get('card_last_4')}")
            print(f"Receipt Number: {result.get('receipt_number')}")
            print(f"Transaction Time: {result.get('transaction_time')}")
            print(f"Message: {result.get('message')}")
            
            print("\n📋 FULL RESPONSE:")
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        except NedarimDebitCardError as e:
            print("❌ FAILED!")
            print(f"Error Message: {e.message}")
            print(f"Error Code: {e.error_code}")
            print(f"Details: {e.details}")
            
        except Exception as e:
            print("❌ UNEXPECTED ERROR!")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
        
        # Wait between requests
        if i < len(test_cases):
            print("Waiting 2 seconds before next test...")
            await asyncio.sleep(2)
    
    print("=" * 80)
    print("HK CORRECT TESTS COMPLETED")
    print("=" * 80)
    print()
    print("📝 Summary:")
    print("   HK = Standing order (הוראת קבע)")
    print("   Amount = Monthly payment amount")
    print("   Tashloumim = Number of months to charge")
    print("   If Tashloumim is empty/not sent = Infinite standing order")
    print()


if __name__ == "__main__":
    asyncio.run(test_hk_correct())
