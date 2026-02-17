"""Test HK via NedarimDebitCardService - verifies routing to DebitKeva.aspx"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from services.nedarim_debit_card import NedarimDebitCardService

    service = NedarimDebitCardService()
    
    print("=== Testing HK (DebitKeva) via service ===")
    print("Monthly: 5.50, Months: 3, Expected total: 16.50")
    
    result = await service.charge_card(
        client_name="Test HK Service",
        card_number="4580170008989957",
        expiry="0129",
        cvv="714",
        amount=5.50,
        installments=3,
        payment_type="HK",
        email="test@example.com",
        phone="0501234567",
        comments="Test HK via service",
    )
    
    print(f"\n=== RESULT ===")
    for k, v in result.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
