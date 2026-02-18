"""
עיבוד קובץ HTML של קמפיין מימוש הטבה מימות המשיח
חילוץ טלפונים ועדכון היסטוריה לפי בחירת המתקשר (P050)
"""
import asyncio
import asyncpg
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime
import sys
sys.path.insert(0, r'c:\Users\admin\kinyan-crm-new')
from utils.phone import normalize_phone

DB_URL = "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
HTML_FILE = r"C:\Users\admin\Downloads\ApprovalAll (12).html"


def parse_html_table(html_content: str) -> list[dict]:
    """
    מפרק את טבלת ה-HTML ומחלץ את כל השורות.
    מחזיר רשימה של דיקטים עם: phone, date, time, p050_value
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='report')
    
    if not table:
        print("❌ לא נמצאה טבלה בקובץ!")
        return []
    
    rows = []
    tbody = table.find('tbody')
    
    if not tbody:
        print("❌ לא נמצא tbody בטבלה!")
        return []
    
    for tr in tbody.find_all('tr'):
        cells = tr.find_all('td')
        if len(cells) >= 12:
            # עמודות: מצב הזמנה, שלוחה, מערכת, IncomingDID, טלפון, תאריך, שעה, תאריך עברי, ערך/שלוחה, הזמנה, הנתונים שהתקבלו, P050
            phone_raw = cells[4].get_text(strip=True)
            date_str = cells[5].get_text(strip=True)
            time_str = cells[6].get_text(strip=True)
            p050_value = cells[11].get_text(strip=True)
            
            rows.append({
                'phone_raw': phone_raw,
                'date': date_str,
                'time': time_str,
                'p050': p050_value,
            })
    
    return rows


def get_interaction_text(p050_value: str, count: int, last_date: str) -> str:
    """
    מחזיר את טקסט ה-interaction לפי ערך P050.
    
    P050 = 1: רוצה פרטים מנציג
    P050 = 5: ביקש הסרה 5
    P050 = 9: ביקש הסרה 9
    """
    base_text = "חזר לקמפיין מימוש הטבה"
    
    if p050_value == "1":
        action = "רוצה פרטים מנציג"
    elif p050_value == "5":
        action = "ביקש הסרה 5"
    elif p050_value == "9":
        action = "ביקש הסרה 9"
    else:
        action = f"בחירה {p050_value}"
    
    result = f"{base_text} - {action}"
    
    if count > 1:
        result += f" ({count} פעמים)"
    
    result += f"\nתאריך אחרון: {last_date}"
    
    return result


def process_phone_data(rows: list[dict]) -> dict:
    """
    מעבד את הטלפונים:
    1. מנרמל כל טלפון
    2. מקבץ לפי טלפון (כפילויות)
    3. שומר תאריך ראשון (created_at), אחרון, ספירה, וערך P050 האחרון
    
    מחזיר: {normalized_phone: {'count': X, 'first_datetime': datetime, 'last_date': 'DD/MM/YYYY HH:MM:SS', 'p050': 'X'}}
    """
    phone_data = defaultdict(lambda: {'count': 0, 'first_datetime': None, 'last_date': None, 'last_datetime': None, 'p050': None})
    
    for row in rows:
        phone_raw = row['phone_raw']
        phone = normalize_phone(phone_raw)
        
        if not phone:
            continue
        
        # פורמט תאריך ושעה
        try:
            date_time_str = f"{row['date']} {row['time']}"
            dt = datetime.strptime(date_time_str, "%d/%m/%Y %H:%M:%S")
        except:
            dt = None
        
        phone_data[phone]['count'] += 1
        
        if dt:
            # שמירת התאריך הראשון (ליצירה)
            if phone_data[phone]['first_datetime'] is None or dt < phone_data[phone]['first_datetime']:
                phone_data[phone]['first_datetime'] = dt
            
            # שמירת התאריך והערך האחרון
            if phone_data[phone]['last_datetime'] is None or dt > phone_data[phone]['last_datetime']:
                phone_data[phone]['last_datetime'] = dt
                phone_data[phone]['last_date'] = date_time_str
                phone_data[phone]['p050'] = row['p050']  # שומר את הערך האחרון
    
    return dict(phone_data)


# הוסר - לא משייכים אוטומטית לאיש מכירות


async def process_leads(phone_data: dict, dry_run=True):
    """
    מעבד את הלידים:
    - לידים קיימים: מוסיף interaction להיסטוריה
    - לידים חדשים: יוצר ליד חדש
    """
    print("=" * 80)
    print("עיבוד לידים מקובץ IVR - קמפיין מימוש הטבה")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  מצב DRY RUN - לא יעדכן כלום ב-DB")
    else:
        print("\n🔴 מצב LIVE - יעדכן ויצור לידים!")
    
    conn = await asyncpg.connect(DB_URL)
    
    try:
        print(f"\n📊 סה\"כ טלפונים ייחודיים: {len(phone_data)}")
        
        # בדיקה אילו טלפונים קיימים
        phones_list = list(phone_data.keys())
        existing_leads = await conn.fetch("""
            SELECT id, phone, full_name, status
            FROM leads
            WHERE phone = ANY($1)
        """, phones_list)
        
        existing_phones = {lead['phone']: lead for lead in existing_leads}
        
        print(f"✅ לידים קיימים: {len(existing_phones)}")
        print(f"🆕 לידים חדשים ליצירה: {len(phone_data) - len(existing_phones)}")
        
        # ספירת בחירות
        p050_stats = defaultdict(int)
        for data in phone_data.values():
            p050_stats[data['p050']] += 1
        
        print("\n📊 התפלגות בחירות:")
        for p050, count in sorted(p050_stats.items()):
            if p050 == "1":
                print(f"   1 (רוצה פרטים מנציג): {count}")
            elif p050 == "5":
                print(f"   5 (ביקש הסרה): {count}")
            elif p050 == "9":
                print(f"   9 (ביקש הסרה): {count}")
            else:
                print(f"   {p050}: {count}")
        
        stats = {
            'existing_updated': 0,
            'new_created': 0,
            'interactions_added': 0,
        }
        
        print("\n" + "=" * 80)
        print("מעבד לידים...")
        print("=" * 80)
        
        for phone, data in phone_data.items():
            count = data['count']
            last_date = data['last_date']
            first_datetime = data['first_datetime']
            p050 = data['p050']
            
            interaction_text = get_interaction_text(p050, count, last_date)
            
            if phone in existing_phones:
                # ליד קיים - עדכון היסטוריה
                lead = existing_phones[phone]
                
                print(f"\n✅ קיים: {lead['full_name']} ({phone})")
                print(f"   📞 {count} פעמים, אחרון: {last_date}, P050={p050}")
                
                if not dry_run:
                    # הוספת interaction
                    await conn.execute("""
                        INSERT INTO lead_interactions 
                        (lead_id, interaction_type, description, created_at)
                        VALUES ($1, $2, $3, NOW())
                    """, lead['id'], 'שיחה נכנסת', interaction_text)
                    
                    stats['interactions_added'] += 1
                
                stats['existing_updated'] += 1
            
            else:
                # ליד חדש - יצירה
                print(f"\n🆕 חדש: {phone}")
                print(f"   📞 {count} פעמים, אחרון: {last_date}, P050={p050}")
                
                if not dry_run:
                    # יצירת ליד חדש עם תאריך מה-HTML
                    lead_id = await conn.fetchval("""
                        INSERT INTO leads 
                        (full_name, phone, status, source_type, source_name, 
                         notes, first_payment, first_lesson, approved_terms, follow_up_count,
                         payment_completed, payment_verified, kinyan_signed, shipping_details_complete,
                         student_chat_added, handoff_to_manager, handoff_completed, 
                         conversion_checklist_complete, created_at, arrival_date)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                        RETURNING id
                    """, 
                        'ליד ללא שם',  # full_name
                        phone,  # phone
                        'ליד חדש',  # status
                        'IVR',  # source_type
                        'קמפיין מימוש הטבה - ימות המשיח',  # source_name
                        f"קמפיין מימוש הטבה - {count} פעמים\nבחירה אחרונה: P050={p050}\nתאריך אחרון: {last_date}",  # notes
                        False,  # first_payment
                        False,  # first_lesson
                        False,  # approved_terms
                        0,  # follow_up_count
                        False,  # payment_completed
                        False,  # payment_verified
                        False,  # kinyan_signed
                        False,  # shipping_details_complete
                        False,  # student_chat_added
                        False,  # handoff_to_manager
                        False,  # handoff_completed
                        False,  # conversion_checklist_complete
                        first_datetime,  # created_at - מה-HTML!
                        first_datetime  # arrival_date - מה-HTML!
                    )
                    
                    # הוספת interaction ראשוני
                    await conn.execute("""
                        INSERT INTO lead_interactions 
                        (lead_id, interaction_type, description, created_at)
                        VALUES ($1, $2, $3, NOW())
                    """, lead_id, 'שיחה נכנסת', interaction_text)
                    
                    stats['interactions_added'] += 1
                
                stats['new_created'] += 1
        
        # סיכום
        print("\n" + "=" * 80)
        print("סיכום:")
        print("=" * 80)
        print(f"📊 סה\"כ טלפונים: {len(phone_data)}")
        print(f"✅ לידים קיימים שעודכנו: {stats['existing_updated']}")
        print(f"🆕 לידים חדשים שנוצרו: {stats['new_created']}")
        
        if not dry_run:
            print(f"💬 Interactions שנוספו: {stats['interactions_added']}")
            print("\n✅ עיבוד הושלם בהצלחה!")
        else:
            print("\n⚠️  זה היה DRY RUN - לא עודכן כלום")
            print("להרצה אמיתית: הרץ עם --live")
        
    finally:
        await conn.close()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="עיבוד קובץ IVR - קמפיין מימוש הטבה")
    parser.add_argument("--live", action="store_true", help="הרצה אמיתית (לא dry-run)")
    args = parser.parse_args()
    
    print("📂 קורא קובץ HTML...")
    try:
        with open(HTML_FILE, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ שגיאה בקריאת הקובץ: {e}")
        return
    
    print("🔍 מפרק טבלה...")
    rows = parse_html_table(html_content)
    
    if not rows:
        print("❌ לא נמצאו שורות בטבלה!")
        return
    
    print(f"✅ נמצאו {len(rows)} שורות בטבלה")
    
    print("🔄 מעבד ומנרמל טלפונים...")
    phone_data = process_phone_data(rows)
    
    print(f"✅ {len(phone_data)} טלפונים ייחודיים אחרי נירמול")
    
    # הצגת דוגמאות
    print("\n📋 דוגמאות (5 ראשונות):")
    for i, (phone, data) in enumerate(list(phone_data.items())[:5]):
        p050_desc = "רוצה פרטים" if data['p050'] == "1" else f"הסרה {data['p050']}" if data['p050'] in ["5", "9"] else data['p050']
        print(f"  {i+1}. {phone} - {data['count']} פעמים, P050={data['p050']} ({p050_desc})")
    
    # עיבוד לידים
    await process_leads(phone_data, dry_run=not args.live)


if __name__ == "__main__":
    asyncio.run(main())
