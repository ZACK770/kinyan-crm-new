"""
בדיקת כפילויות שנוצרו מהסקריפטים הקודמים
"""
import asyncio
import asyncpg
from collections import defaultdict

DB_URL = "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"


async def check_duplicates():
    conn = await asyncpg.connect(DB_URL)
    
    try:
        # בדיקת כפילויות שנוצרו היום
        print("=" * 80)
        print("בדיקת כפילויות שנוצרו היום")
        print("=" * 80)
        
        # כל הלידים שנוצרו היום
        today_leads = await conn.fetch("""
            SELECT id, full_name, phone, source_name, created_at
            FROM leads
            WHERE DATE(created_at) = CURRENT_DATE
            ORDER BY phone, created_at
        """)
        
        print(f"\n📊 נמצאו {len(today_leads)} לידים שנוצרו היום")
        
        # קיבוץ לפי טלפון
        phone_groups = defaultdict(list)
        for lead in today_leads:
            phone_groups[lead['phone']].append(lead)
        
        # מציאת כפילויות
        duplicates = {phone: leads for phone, leads in phone_groups.items() if len(leads) > 1}
        
        if duplicates:
            print(f"\n🔴 נמצאו {len(duplicates)} טלפונים עם כפילויות!")
            print(f"🔴 סה\"כ {sum(len(leads) for leads in duplicates.values())} לידים כפולים")
            
            print("\n" + "=" * 80)
            print("דוגמאות לכפילויות:")
            print("=" * 80)
            
            for phone, leads in list(duplicates.items())[:10]:
                print(f"\n📞 {phone} - {len(leads)} לידים:")
                for lead in leads:
                    print(f"   ID {lead['id']}: {lead['full_name']} | {lead['source_name']} | {lead['created_at']}")
        else:
            print("\n✅ לא נמצאו כפילויות!")
        
        # בדיקה כללית של כפילויות במערכת
        print("\n" + "=" * 80)
        print("בדיקה כללית של כפילויות במערכת:")
        print("=" * 80)
        
        all_duplicates = await conn.fetch("""
            SELECT phone, COUNT(*) as count
            FROM leads
            WHERE phone IS NOT NULL AND phone != ''
            GROUP BY phone
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 20
        """)
        
        if all_duplicates:
            print(f"\n🔴 נמצאו {len(all_duplicates)} טלפונים עם כפילויות במערכת!")
            print("\n20 הטלפונים הכפולים ביותר:")
            for dup in all_duplicates:
                print(f"   {dup['phone']}: {dup['count']} לידים")
        else:
            print("\n✅ אין כפילויות במערכת!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_duplicates())
