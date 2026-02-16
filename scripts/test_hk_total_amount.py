"""
Test script for HK with TOTAL amount (not monthly) + Tashloumim
Testing if HK needs total amount and Tashloumim divides it
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


async def test_hk_with_total_amount():
    """Test HK with TOTAL amount + Tashloumim (not monthly amount)"""
    
    print("=" * 80)
    print("TEST: HK with TOTAL Amount + Tashloumim")
    print("Sending TOTAL amount (not monthly) and letting Tashloumim divide it")
    print("=" * 80)
    
    service = NedarimDebitCardService()
    
    # Test card details (not real/active)
    card_number = "5326141204526337"
    expiry = "1030"
    cvv = "809"
    
    # Test scenarios - sending TOTAL amount with installments
    test_cases = [
        {
            "name": "HK - סה\"כ ₪300 / 3 תשלומים",
            "payment_type": "HK",
            "total_amount": 300.0,
            "installments": 3,
        },
        {
            "name": "HK - סה\"כ ₪600 / 6 תשלומים",
            "payment_type": "HK",
            "total_amount": 600.0,
            "installments": 6,
        },
        {
            "name": "HK - סה\"כ ₪1200 / 12 תשלומים",
            "payment_type": "HK",
            "total_amount": 1200.0,
            "installments": 12,
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test Case {i}: {test_case['name']}")
        print(f"{'─' * 80}")
        print(f"Payment Type: {test_case['payment_type']}")
        print(f"Total Amount: ₪{test_case['total_amount']}")
        print(f"Installments: {test_case['installments']}")
        print(f"Expected Monthly: ₪{test_case['total_amount'] / test_case['installments']}")
        print()
        print("⚠️  IMPORTANT: Sending TOTAL amount, NOT monthly")
        print(f"   Amount=₪{test_case['total_amount']} with Tashloumim={test_case['installments']}")
        print()
        
        try:
            # Send TOTAL amount (not monthly) with installments
            result = await service.charge_card(
                client_name="Test User - HK Total Amount",
                card_number=card_number,
                expiry=expiry,
                cvv=cvv,
                amount=test_case['total_amount'],  # TOTAL amount!
                installments=test_case['installments'],
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
    print("HK WITH TOTAL AMOUNT TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_hk_with_total_amount())
