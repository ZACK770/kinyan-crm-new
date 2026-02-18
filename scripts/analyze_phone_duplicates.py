"""
ניתוח כפילויות טלפון במערכת - מספרים עם/בלי 0 בהתחלה
"""
import asyncio
import asyncpg
from collections import defaultdict

DB_URL = "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"


async def analyze_duplicates():
    print("=" * 80)
    print("ניתוח כפילויות טלפון במערכת")
    print("=" * 80)
    
    conn = await asyncpg.connect(DB_URL)
    
    try:
        # שליפת כל הטלפונים מ-leads
        print("\n🔍 שולף טלפונים מטבלת leads...")
        leads = await conn.fetch("""
            SELECT id, full_name, phone, status, created_at
            FROM leads
            WHERE phone IS NOT NULL AND phone != ''
            ORDER BY phone
        """)
        
        print(f"✅ נמצאו {len(leads)} לידים עם טלפון")
        
        # מיפוי: טלפון מנורמל -> רשימת לידים
        phone_map = defaultdict(list)
        
        for lead in leads:
            phone = lead['phone']
            # נירמול פשוט - הסרת 0 מההתחלה
            normalized = phone.lstrip('0')
            phone_map[normalized].append({
                'id': lead['id'],
                'name': lead['full_name'],
                'phone': phone,
                'status': lead['status'],
                'created_at': lead['created_at']
            })
        
        # מציאת כפילויות
        duplicates = {k: v for k, v in phone_map.items() if len(v) > 1}
        
        print(f"\n📊 נמצאו {len(duplicates)} קבוצות כפילויות")
        
        if duplicates:
            print("\n" + "=" * 80)
            print("דוגמאות לכפילויות:")
            print("=" * 80)
            
            count = 0
            for normalized, group in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
                if count >= 20:  # מציג רק 20 ראשונות
                    break
                count += 1
                
                print(f"\n🔴 קבוצה {count}: {len(group)} לידים עם מספר {normalized}")
                for lead in group:
                    print(f"   ID {lead['id']}: {lead['name']}")
                    print(f"      טלפון: {lead['phone']} | סטטוס: {lead['status']}")
                    print(f"      נוצר: {lead['created_at']}")
        
        # סטטיסטיקה
        total_duplicates = sum(len(group) for group in duplicates.values())
        unique_leads = len(leads) - total_duplicates + len(duplicates)
        
        print("\n" + "=" * 80)
        print("סיכום:")
        print("=" * 80)
        print(f"📊 סה\"כ לידים: {len(leads)}")
        print(f"🔴 לידים כפולים: {total_duplicates}")
        print(f"✅ לידים ייחודיים (אחרי מיזוג): {unique_leads}")
        print(f"📉 ניתן לחסוך: {total_duplicates - len(duplicates)} רשומות")
        
        # בדיקת students
        print("\n" + "=" * 80)
        print("בדיקת טבלת students:")
        print("=" * 80)
        
        students = await conn.fetch("""
            SELECT id, full_name, phone
            FROM students
            WHERE phone IS NOT NULL AND phone != ''
            ORDER BY phone
        """)
        
        print(f"✅ נמצאו {len(students)} תלמידים עם טלפון")
        
        student_phone_map = defaultdict(list)
        for student in students:
            phone = student['phone']
            normalized = phone.lstrip('0')
            student_phone_map[normalized].append({
                'id': student['id'],
                'name': student['full_name'],
                'phone': phone
            })
        
        student_duplicates = {k: v for k, v in student_phone_map.items() if len(v) > 1}
        print(f"🔴 כפילויות בתלמידים: {len(student_duplicates)} קבוצות")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(analyze_duplicates())
