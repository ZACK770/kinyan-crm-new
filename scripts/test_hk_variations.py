"""
Test HK variations - find what combination creates a real HK (standing order).
The successful test (confirmation 0212274) did NOT send Param2 or CallBack.
"""
import asyncio
import sys
import os
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new')
os.environ.setdefault('NEDARIM_MOSAD_ID', '7009959')
os.environ.setdefault('NEDARIM_API_PASSWORD', 'ou946')

import httpx

CARD = "4580170008989957"
EXPIRY = "0129"
CVV = "714"
MOSAD = "7009959"
API_PWD = "ou946"
URL = "https://www.matara.pro/nedarimplus/V6/Files/WebServices/DebitCard.aspx"


async def send_raw(name, payload):
    safe = {k: v for k, v in payload.items()}
    safe['CardNumber'] = f"****{safe['CardNumber'][-4:]}"
    safe['CVV'] = '***'
    safe['ApiPassword'] = '***'

    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Payload: {json.dumps(safe, ensure_ascii=False, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(URL, data=payload,
                headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
            resp.raise_for_status()
            result = resp.json()

        status = result.get('Status', '?')
        tx_type = result.get('TransactionType', '?')
        keva_id = result.get('KevaId', '')
        confirm = result.get('Confirmation', '')
        tash = result.get('Tashloumim', '?')
        credit = result.get('CreditTerms', '?')
        amount = result.get('Amount', '?')

        is_hk = tx_type != 'רגיל' or keva_id != ''

        print(f"\nRESULT: {'OK' if status == 'OK' else 'FAIL - ' + result.get('Message', '?')}")
        if status == 'OK':
            print(f"  TransactionType: {tx_type}  {'<-- HK!' if is_hk else '<-- RAGIL (not HK!)'}")
            print(f"  KevaId: {keva_id or '(empty)'}  {'<-- HK confirmed!' if keva_id else '<-- NO HK'}")
            print(f"  Confirmation: {confirm}")
            print(f"  Amount: {amount}")
            print(f"  Tashloumim: {tash}")
            print(f"  CreditTerms: {credit}")

        if is_hk:
            print(f"\n  *** SUCCESS - THIS IS A REAL HK! ***")

        return result
    except Exception as e:
        print(f"\nERROR: {e}")
        return None


async def main():
    print("Testing HK variations with real card ****9957")
    print("Amount: 5 ILS, looking for real HK (standing order)")

    base = {
        'Mosad': MOSAD,
        'ApiPassword': API_PWD,
        'CardNumber': CARD,
        'Tokef': EXPIRY,
        'CVV': CVV,
        'Currency': '1',
        'AjaxId': str(int(time.time() * 1000)),
    }

    # Test 1: Exact same as the working script (no Param2, no CallBack)
    print("\n\n" + "#"*70)
    print("# TEST 1: Exact replica of working script (no Param2/CallBack)")
    print("#"*70)
    p = {**base,
        'ClientName': 'Test HK Variation 1',
        'Mail': 'test@example.com',
        'Phone': '0501234567',
        'Amount': '3.00',
        'PaymentType': 'HK',
        'Avour': 'Test 1 - no callback no param2',
        'Groupe': '',
        'Param1': '',
        'Tashlumim': '2',
    }
    await send_raw("HK minimal (like working script) - 3 ILS", p)
    await asyncio.sleep(3)

    # Test 2: Add Param2 + CallBack (what our code sends)
    print("\n\n" + "#"*70)
    print("# TEST 2: HK + Param2 + CallBack (current code)")
    print("#"*70)
    base['AjaxId'] = str(int(time.time() * 1000))
    p = {**base,
        'ClientName': 'Test HK Variation 2',
        'Mail': 'test@example.com',
        'Phone': '0501234567',
        'Amount': '4.00',
        'PaymentType': 'HK',
        'Avour': 'Test 2 - with param2 and callback',
        'Groupe': '',
        'Param1': '',
        'Param2': '4558',
        'CallBack': 'https://kinyan-crm-new-1.onrender.com/webhooks/nedarim-debitcard',
        'Tashlumim': '2',
    }
    await send_raw("HK + Param2 + CallBack (current code) - 4 ILS", p)
    await asyncio.sleep(3)

    # Test 3: Tashloumim with 'ou' spelling (old code used this)
    print("\n\n" + "#"*70)
    print("# TEST 3: HK + Tashloumim (with 'ou' spelling)")
    print("#"*70)
    base['AjaxId'] = str(int(time.time() * 1000))
    p = {**base,
        'ClientName': 'Test HK Variation 3',
        'Mail': 'test@example.com',
        'Phone': '0501234567',
        'Amount': '6.00',
        'PaymentType': 'HK',
        'Avour': 'Test 3 - Tashloumim with ou',
        'Groupe': '',
        'Param1': '',
        'Tashloumim': '2',
    }
    await send_raw("HK + Tashloumim (ou spelling) - 6 ILS", p)
    await asyncio.sleep(3)

    # Test 4: HK without ANY Tashlumim/Tashloumim (infinite standing order)
    print("\n\n" + "#"*70)
    print("# TEST 4: HK without Tashlumim at all (infinite)")
    print("#"*70)
    base['AjaxId'] = str(int(time.time() * 1000))
    p = {**base,
        'ClientName': 'Test HK Variation 4',
        'Mail': 'test@example.com',
        'Phone': '0501234567',
        'Amount': '7.00',
        'PaymentType': 'HK',
        'Avour': 'Test 4 - no tashlumim at all',
        'Groupe': '',
        'Param1': '',
    }
    await send_raw("HK without Tashlumim (infinite) - 7 ILS", p)
    await asyncio.sleep(3)

    # Test 5: PaymentType = 'Ragil' (not 'RAGIL') - check case sensitivity
    print("\n\n" + "#"*70)
    print("# TEST 5: PaymentType='Ragil' (lowercase) + Tashlumim=2")
    print("#"*70)
    base['AjaxId'] = str(int(time.time() * 1000))
    p = {**base,
        'ClientName': 'Test HK Variation 5',
        'Mail': 'test@example.com',
        'Phone': '0501234567',
        'Amount': '8.00',
        'PaymentType': 'Ragil',
        'Avour': 'Test 5 - Ragil lowercase with tashlumim',
        'Groupe': '',
        'Param1': '',
        'Tashlumim': '2',
    }
    await send_raw("Ragil (lowercase) + Tashlumim=2 - 8 ILS", p)

    print("\n\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
