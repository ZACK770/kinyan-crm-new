"""
מחיקת לידים שנוצרו היום מהסקריפטים (בטעות עם תאריך שגוי)
"""
import asyncio
import asyncpg

DB_URL = "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"


async def delete_todays_leads():
    conn = await asyncpg.connect(DB_URL)
    
    try:
        # מציאת לידים שנוצרו היום מ-IVR
        leads = await conn.fetch("""
            SELECT id, full_name, phone, source_name, created_at
            FROM leads
            WHERE DATE(created_at) = CURRENT_DATE
              AND (source_name LIKE '%ימות המשיח%' OR source_name LIKE '%IVR%')
            ORDER BY id
        """)
        
        print("=" * 80)
        print(f"נמצאו {len(leads)} לידים שנוצרו היום מ-IVR")
        print("=" * 80)
        
        if not leads:
            print("✅ אין לידים למחיקה")
            return
        
        # הצגת דוגמאות
        print("\nדוגמאות (10 ראשונות):")
        for lead in leads[:10]:
            print(f"  ID {lead['id']}: {lead['full_name']} | {lead['phone']} | {lead['source_name']}")
        
        # אישור
        print(f"\n⚠️  עומד למחוק {len(leads)} לידים!")
        response = input("האם להמשיך? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ בוטל")
            return
        
        # מחיקת interactions קשורים
        lead_ids = [lead['id'] for lead in leads]
        
        interactions_deleted = await conn.execute("""
            DELETE FROM lead_interactions
            WHERE lead_id = ANY($1)
        """, lead_ids)
        
        print(f"\n🗑️  נמחקו {interactions_deleted.split()[-1]} interactions")
        
        # מחיקת הלידים
        leads_deleted = await conn.execute("""
            DELETE FROM leads
            WHERE id = ANY($1)
        """, lead_ids)
        
        print(f"🗑️  נמחקו {leads_deleted.split()[-1]} לידים")
        print("\n✅ מחיקה הושלמה!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(delete_todays_leads())
