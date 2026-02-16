"""Verify HK with Tashloumim (ou spelling) works."""
import asyncio, time, json, httpx

async def main():
    payload = {
        'Mosad': '7009959', 'ApiPassword': 'ou946',
        'ClientName': 'Verify HK', 'Mail': 'test@example.com', 'Phone': '0501234567',
        'CardNumber': '4580170008989957', 'Tokef': '0129', 'CVV': '714',
        'Amount': '16.50', 'Currency': '1', 'PaymentType': 'HK',
        'Avour': 'Verify HK Tashloumim ou', 'Groupe': '', 'Param1': '',
        'AjaxId': str(int(time.time() * 1000)),
        'Tashloumim': '3',
    }
    print(f"Sending: PaymentType=HK, Amount=13.50, Tashloumim=3 (ou spelling)")
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post("https://www.matara.pro/nedarimplus/V6/Files/WebServices/DebitCard.aspx",
            data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
        res = r.json()
    print(f"Status: {res.get('Status')}")
    print(f"TransactionType: {res.get('TransactionType')}")
    print(f"Tashloumim: {res.get('Tashloumim')}")
    print(f"CreditTerms: {res.get('CreditTerms')}")
    print(f"FirstTashloum: {res.get('FirstTashloum')}")
    print(f"Amount: {res.get('Amount')}")
    print(f"Confirmation: {res.get('Confirmation')}")
    print(f"KevaId: {res.get('KevaId') or '(empty)'}")
    if res.get('Status') != 'OK':
        print(f"Message: {res.get('Message')}")

if __name__ == "__main__":
    asyncio.run(main())
