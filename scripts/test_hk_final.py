"""
Test ALL variations of PaymentType + Tashloumim + Amount to find real HK.
Only changing the core payment parameters - nothing else.
Each test uses a unique amount to avoid duplicate errors.
"""
import asyncio
import time
import json
import httpx

URL = "https://www.matara.pro/nedarimplus/V6/Files/WebServices/DebitCard.aspx"
CARD = "4580170008989957"
EXPIRY = "0129"
CVV = "714"

n = 0

async def t(desc, payment_type, amount, tashloumim_field=None, tashloumim_val=None):
    global n
    n += 1
    p = {
        'Mosad': '7009959', 'ApiPassword': 'ou946',
        'ClientName': f'Test {n}', 'Mail': '', 'Phone': '0501234567',
        'CardNumber': CARD, 'Tokef': EXPIRY, 'CVV': CVV,
        'Amount': f'{amount:.2f}', 'Currency': '1',
        'PaymentType': payment_type,
        'Avour': desc, 'Groupe': '', 'Param1': '',
        'AjaxId': str(int(time.time() * 1000)),
    }
    if tashloumim_field and tashloumim_val:
        p[tashloumim_field] = str(tashloumim_val)

    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post(URL, data=p,
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
        res = r.json()

    s = res.get('Status','?')
    tt = res.get('TransactionType','?')
    ki = res.get('KevaId','')
    hk = bool(ki) or 'קבע' in tt
    sym = 'HK!!!' if hk else ('OK' if s=='OK' else 'FAIL')

    line = f"[{sym:5}] #{n:2} | PT={payment_type:5} | Amt={amount:6.2f}"
    if tashloumim_field:
        line += f" | {tashloumim_field}={tashloumim_val}"
    else:
        line += f" | (no tashloumim)"
    
    if s == 'OK':
        line += f" => Type={tt}, KevaId={ki or '-'}, Tash={res.get('Tashloumim','?')}, Credit={res.get('CreditTerms','?')}"
    else:
        line += f" => {res.get('Message','?')[:50]}"
    
    print(line)
    if hk:
        print(f"\n*** FOUND HK! Full response: ***")
        print(json.dumps(res, ensure_ascii=False, indent=2))
    return hk


async def main():
    print("="*80)
    print("HK VARIATION TEST - PaymentType / Amount / Tashloumim combinations")
    print("="*80)
    
    amt = 20  # starting amount, +1 each test
    found = False

    # --- A: HK without any tashloumim, different amounts ---
    print("\n--- A: HK, no tashloumim ---")
    for a in [21, 22, 50]:
        if await t(f"HK no-tash {a}", 'HK', a): found = True; break
        await asyncio.sleep(2)

    # --- B: HK + Tashloumim (ou) = different values ---
    print("\n--- B: HK + Tashloumim (ou spelling) ---")
    for tash in [2, 3, 6, 12]:
        amt = 23 + tash
        if await t(f"HK+Tashloumim={tash}", 'HK', amt, 'Tashloumim', tash): found = True; break
        await asyncio.sleep(2)

    # --- C: HK + Tashlumim (no ou) = different values ---
    print("\n--- C: HK + Tashlumim (no ou spelling) ---")
    for tash in [2, 3]:
        amt = 30 + tash
        if await t(f"HK+Tashlumim={tash}", 'HK', amt, 'Tashlumim', tash): found = True; break
        await asyncio.sleep(2)

    # --- D: Ragil + Tashloumim ---
    print("\n--- D: Ragil + Tashloumim ---")
    for tash in [2, 3]:
        amt = 35 + tash
        if await t(f"Ragil+Tashloumim={tash}", 'Ragil', amt, 'Tashloumim', tash): found = True; break
        await asyncio.sleep(2)

    # --- E: RAGIL + Tashloumim ---
    print("\n--- E: RAGIL + Tashloumim ---")
    for tash in [2, 3]:
        amt = 40 + tash
        if await t(f"RAGIL+Tashloumim={tash}", 'RAGIL', amt, 'Tashloumim', tash): found = True; break
        await asyncio.sleep(2)

    # --- F: HK + big amounts (maybe minimum issue) ---
    print("\n--- F: HK + Tashloumim + bigger amounts ---")
    for a, tash in [(100, 2), (100, 3), (200, 6)]:
        if await t(f"HK Amt={a} Tash={tash}", 'HK', a, 'Tashloumim', tash): found = True; break
        await asyncio.sleep(2)

    # --- G: HK + Day parameter ---
    print("\n--- G: HK + Day ---")
    amt = 55
    p = {
        'Mosad': '7009959', 'ApiPassword': 'ou946',
        'ClientName': 'Test Day', 'Mail': '', 'Phone': '0501234567',
        'CardNumber': CARD, 'Tokef': EXPIRY, 'CVV': CVV,
        'Amount': f'{amt:.2f}', 'Currency': '1',
        'PaymentType': 'HK', 'Tashloumim': '3', 'Day': '15',
        'Avour': 'HK+Day+Tashloumim', 'Groupe': '', 'Param1': '',
        'AjaxId': str(int(time.time() * 1000)),
    }
    async with httpx.AsyncClient(timeout=30.0) as c:
        r = await c.post(URL, data=p,
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
        res = r.json()
    s = res.get('Status','?')
    ki = res.get('KevaId','')
    tt = res.get('TransactionType','?')
    hk = bool(ki) or 'קבע' in tt
    sym = 'HK!!!' if hk else ('OK' if s=='OK' else 'FAIL')
    line = f"[{sym:5}] HK+Day=15+Tashloumim=3, Amt=55"
    if s == 'OK':
        line += f" => Type={tt}, KevaId={ki or '-'}, Tash={res.get('Tashloumim','?')}"
    else:
        line += f" => {res.get('Message','?')[:50]}"
    print(line)
    if hk:
        found = True
        print(json.dumps(res, ensure_ascii=False, indent=2))

    print("\n" + "="*80)
    if found:
        print("SUCCESS! Found real HK!")
    else:
        print("NO REAL HK FOUND via DebitCard.aspx")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
