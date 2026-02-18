"""
מיזוג כפילויות טלפון - לידים עם אותו מספר (עם/בלי 0)
לוגיקה: שומר את הליד עם הכי הרבה מידע, ממזג שדות, מעביר קשרים
"""
import asyncio
import asyncpg
from collections import defaultdict
from datetime import datetime

DB_URL = "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"


def score_lead(lead: dict) -> int:
    """
    מחשב ציון לליד לפי כמות המידע שיש בו.
    ליד עם יותר מידע = ציון גבוה יותר.
    """
    score = 0
    
    # שדות בסיסיים (1 נקודה לכל שדה מלא)
    if lead.get('full_name') and lead['full_name'] not in ['ליד ללא שם', 'יש להשלים פרטים', 'חסר פרטים', None, '']:
        score += 2
    if lead.get('family_name'):
        score += 1
    if lead.get('email'):
        score += 1
    if lead.get('phone2'):
        score += 1
    if lead.get('city'):
        score += 1
    if lead.get('address'):
        score += 1
    if lead.get('id_number'):
        score += 1
    if lead.get('notes'):
        score += 1
    
    # שדות חשובים (2 נקודות)
    if lead.get('salesperson_id'):
        score += 2
    if lead.get('course_id'):
        score += 2
    if lead.get('campaign_id'):
        score += 2
    
    # סטטוס מתקדם (נקודות לפי התקדמות)
    status = lead.get('status', '')
    if status == 'תלמיד פעיל':
        score += 10
    elif status == 'נסלק':
        score += 5
    elif status == 'ליד בתהליך':
        score += 3
    elif status == 'חיוג ראשון':
        score += 2
    
    # שדות המרה
    if lead.get('payment_completed'):
        score += 5
    if lead.get('kinyan_signed'):
        score += 3
    if lead.get('student_id'):
        score += 10
    
    # תאריך יצירה - ליד ישן יותר = עדיפות קלה
    if lead.get('created_at'):
        # ליד ישן מקבל בונוס קטן
        score += 1
    
    return score


def merge_field(field_name: str, keep_value, other_value):
    """
    מיזוג שדה בודד - מחזיר את הערך המועדף.
    """
    # אם אחד מהם None או ריק - קח את השני
    if not keep_value or keep_value in ['', 'ליד ללא שם', 'יש להשלים פרטים', 'חסר פרטים']:
        return other_value
    if not other_value or other_value in ['', 'ליד ללא שם', 'יש להשלים פרטים', 'חסר פרטים']:
        return keep_value
    
    # אם שניהם זהים - קח אחד
    if keep_value == other_value:
        return keep_value
    
    # שדות מיוחדים
    if field_name == 'notes':
        # הערות - צירוף
        return f"{keep_value}\n---\n{other_value}"
    
    if field_name == 'created_at':
        # תאריך יצירה - קח את המוקדם יותר
        if isinstance(keep_value, datetime) and isinstance(other_value, datetime):
            return min(keep_value, other_value)
        return keep_value
    
    if field_name == 'arrival_date':
        # תאריך הגעה - קח את המוקדם יותר
        if isinstance(keep_value, datetime) and isinstance(other_value, datetime):
            return min(keep_value, other_value)
        return keep_value
    
    # ברירת מחדל - שמור את הערך של הליד שנשמר
    return keep_value


async def merge_duplicates(dry_run=True):
    """
    מיזוג כפילויות טלפון.
    
    Args:
        dry_run: אם True, רק מציג מה יעשה בלי לעדכן בפועל
    """
    print("=" * 80)
    print("מיזוג כפילויות טלפון במערכת")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  מצב DRY RUN - לא יעדכן כלום ב-DB")
    else:
        print("\n🔴 מצב LIVE - ימזג ויימחק רשומות!")
    
    conn = await asyncpg.connect(DB_URL)
    
    try:
        # 1. שליפת כל הלידים
        print("\n🔍 שולף לידים...")
        leads = await conn.fetch("""
            SELECT id, full_name, family_name, phone, phone2, email, city, address, 
                   id_number, notes, status, salesperson_id, course_id, campaign_id,
                   payment_completed, kinyan_signed, student_id, created_at, arrival_date,
                   source_type, source_name, campaign_name, lead_response, last_contact_date
            FROM leads
            WHERE phone IS NOT NULL AND phone != ''
            ORDER BY phone
        """)
        
        print(f"✅ נמצאו {len(leads)} לידים")
        
        # 2. מיפוי לפי טלפון מנורמל
        phone_map = defaultdict(list)
        for lead in leads:
            phone = lead['phone']
            normalized = phone.lstrip('0')
            phone_map[normalized].append(dict(lead))
        
        # 3. מציאת כפילויות
        duplicates = {k: v for k, v in phone_map.items() if len(v) > 1}
        
        print(f"\n📊 נמצאו {len(duplicates)} קבוצות כפילויות")
        
        if not duplicates:
            print("✅ אין כפילויות למיזוג!")
            return
        
        # 4. מיזוג כל קבוצה
        stats = {
            "merged_groups": 0,
            "leads_kept": 0,
            "leads_deleted": 0,
            "interactions_moved": 0,
            "payments_moved": 0,
            "tasks_moved": 0,
        }
        
        print("\n" + "=" * 80)
        print("מתחיל מיזוג...")
        print("=" * 80)
        
        for normalized, group in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
            if len(group) < 2:
                continue
            
            # מיון לפי ציון (הכי טוב ראשון)
            group_sorted = sorted(group, key=score_lead, reverse=True)
            
            keep_lead = group_sorted[0]
            delete_leads = group_sorted[1:]
            
            print(f"\n🔄 קבוצה: {len(group)} לידים עם מספר {normalized}")
            print(f"   ✅ שומר: ID {keep_lead['id']} - {keep_lead['full_name']} (ציון: {score_lead(keep_lead)})")
            
            for other in delete_leads:
                print(f"   ❌ מוחק: ID {other['id']} - {other['full_name']} (ציון: {score_lead(other)})")
            
            if not dry_run:
                # מיזוג שדות
                merged_data = {}
                for field in ['full_name', 'family_name', 'email', 'phone2', 'city', 'address', 
                             'id_number', 'notes', 'source_type', 'source_name', 'campaign_name',
                             'lead_response', 'created_at', 'arrival_date', 'last_contact_date']:
                    
                    keep_value = keep_lead.get(field)
                    
                    # בדיקה אם יש ערך טוב יותר בלידים האחרים
                    for other in delete_leads:
                        other_value = other.get(field)
                        keep_value = merge_field(field, keep_value, other_value)
                    
                    if keep_value is not None:
                        merged_data[field] = keep_value
                
                # עדכון הליד שנשמר
                if merged_data:
                    set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(merged_data.keys())])
                    values = [keep_lead['id']] + list(merged_data.values())
                    
                    await conn.execute(f"""
                        UPDATE leads
                        SET {set_clause}
                        WHERE id = $1
                    """, *values)
                
                # העברת קשרים
                delete_ids = [lead['id'] for lead in delete_leads]
                
                # Lead interactions
                interactions_moved = await conn.execute("""
                    UPDATE lead_interactions
                    SET lead_id = $1
                    WHERE lead_id = ANY($2)
                """, keep_lead['id'], delete_ids)
                stats["interactions_moved"] += int(interactions_moved.split()[-1])
                
                # Payments
                payments_moved = await conn.execute("""
                    UPDATE payments
                    SET lead_id = $1
                    WHERE lead_id = ANY($2)
                """, keep_lead['id'], delete_ids)
                stats["payments_moved"] += int(payments_moved.split()[-1])
                
                # Sales tasks
                tasks_moved = await conn.execute("""
                    UPDATE sales_tasks
                    SET lead_id = $1
                    WHERE lead_id = ANY($2)
                """, keep_lead['id'], delete_ids)
                stats["tasks_moved"] += int(tasks_moved.split()[-1])
                
                # Lead products
                await conn.execute("""
                    UPDATE lead_products
                    SET lead_id = $1
                    WHERE lead_id = ANY($2)
                """, keep_lead['id'], delete_ids)
                
                # Lead messages
                await conn.execute("""
                    UPDATE lead_messages
                    SET lead_id = $1
                    WHERE lead_id = ANY($2)
                """, keep_lead['id'], delete_ids)
                
                # מחיקת הלידים הכפולים
                await conn.execute("""
                    DELETE FROM leads
                    WHERE id = ANY($1)
                """, delete_ids)
                
                stats["leads_deleted"] += len(delete_ids)
            
            stats["merged_groups"] += 1
            stats["leads_kept"] += 1
        
        # 5. סיכום
        print("\n" + "=" * 80)
        print("סיכום:")
        print("=" * 80)
        print(f"📊 קבוצות שמוזגו: {stats['merged_groups']}")
        print(f"✅ לידים שנשמרו: {stats['leads_kept']}")
        print(f"❌ לידים שנמחקו: {stats['leads_deleted']}")
        
        if not dry_run:
            print(f"🔄 Interactions שהועברו: {stats['interactions_moved']}")
            print(f"💰 Payments שהועברו: {stats['payments_moved']}")
            print(f"📋 Tasks שהועברו: {stats['tasks_moved']}")
            print("\n✅ מיזוג הושלם בהצלחה!")
        else:
            print("\n⚠️  זה היה DRY RUN - לא עודכן כלום")
            print("להרצה אמיתית: הרץ עם --live")
        
    finally:
        await conn.close()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="מיזוג כפילויות טלפון")
    parser.add_argument("--live", action="store_true", help="הרצה אמיתית (לא dry-run)")
    args = parser.parse_args()
    
    await merge_duplicates(dry_run=not args.live)


if __name__ == "__main__":
    asyncio.run(main())
