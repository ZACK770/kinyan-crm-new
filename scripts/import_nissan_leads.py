"""
Import leads from Nissan Telemarketing campaign.

Data format from user:
phone_id | date | course | city | recording_url | message

Usage:
  python scripts/import_nissan_leads.py [--dry-run]
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Optional

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set DB URL if not set
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import SessionLocal
from db.models import Lead

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Data from user - phone_id, date, course, city, recording_url, message
LEADS_DATA = [
    {
        "phone_id": "504107202",
        "date": "19/03/2026",
        "course": "בני ברק",
        "city": "בני ברק", 
        "recording_url": "",
        "message": "ההקלטה מכילה דיבור לא ברור ולא ניתן לתמלל את תוכנה."
    },
    {
        "phone_id": "527170169", 
        "date": "19/03/2026",
        "course": "איסור והיתר",
        "city": "בני ברק",
        "recording_url": "https://drive.google.com/file/d/1gZbLo2wT9okAb6TWTSdcvszsQLGj_aHP/preview",
        "message": ""
    },
    {
        "phone_id": "527657875",
        "date": "19/03/2026", 
        "course": "איסור והיתר",
        "city": "בית שמש",
        "recording_url": "https://drive.google.com/file/d/1nHhzXhf2WG5hW6PXsoK9DbjhvY8gy3dD/preview",
        "message": "ההקלטה קצרה מאוד ואינה מכילה דיבור ברור. נשמע בה רחש קל/קול לא ברור בלבד, ואין בה פרטי לקוח או בקשות.\n\n[רחש קל / קול לא ברור]"
    },
    {
        "phone_id": "504160132",
        "date": "19/03/2026",
        "course": "איסור והיתר", 
        "city": "בני ברק",
        "recording_url": "https://drive.google.com/file/d/1u77Nb0vFEVGNR5FBHXlQv2SyjgoVKP2B/preview",
        "message": "השם יחזקאל ששון.\nרחוב רשב""ם 20, בני ברק."
    },
    {
        "phone_id": "534116350",
        "date": "19/03/2026",
        "course": "טהרה עם שימוש",
        "city": "בני ברק", 
        "recording_url": "https://drive.google.com/file/d/1szqrugTUzgDAarfVq-RP1sbTNgFatWaL/preview",
        "message": "אברהם ישוע ריינינג\nרחוב בר אילן 27 בני ברק"
    },
    {
        "phone_id": "527602501",
        "date": "19/03/2026",
        "course": "טהרה עם שימוש",
        "city": "בית שמש",
        "recording_url": "https://drive.google.com/file/d/1oXNy4EvWe9TSKQgt4McNc1PizigRAsJ_/preview", 
        "message": "שמי אלון אייזנברג. אה, מוצא לדעת מתי מתחיל הקורס של חושטר בבית שמש. ומה הפרטים, מה המחיר וכמה זמן זה לימוד. תודה רבה."
    },
    {
        "phone_id": "556764604",
        "date": "19/03/2026",
        "course": "טהרה עם שימוש",
        "city": "ביתר",
        "recording_url": "https://drive.google.com/file/d/1fF5sNEYxAVemYDnJrwi68xNR78TN8O7c/preview",
        "message": "מאיר נחמן יושקוביץ, אני רוצה הקלדת פרטים, אם אפשר לחזור אליי, תודה רבה. המספר שלי 05566764604."
    },
    {
        "phone_id": "583232456",
        "date": "19/03/2026",
        "course": "מו\"ץ בהלכות שבת",
        "city": "ביתר",
        "recording_url": "https://drive.google.com/file/d/1oA-1NtOmovK3fFuoq6pixThh0qRKNser/preview",
        "message": "שלום וסור, מעניין אותי את המענה ומה התהליך בדיוק. תודה רבה."
    },
    {
        "phone_id": "527681930",
        "date": "19/03/2026", 
        "course": "מו\"ץ בהלכות שבת",
        "city": "בית שמש",
        "recording_url": "https://drive.google.com/file/d/1QUZMlMTyvxwzWLqeNWAhk_1QCzed_jPc/preview",
        "message": "יעקב אלפר, התקשרתי כדי לקבל מידע על הקורס. לא הצלחתי עד היום להשיג את המידע. אני אשמח לקבל אותו, כי אני כן מאוד מתעניין ב בהלכות שבת. תודה רבה. 0527681930. יישר כוח."
    },
    {
        "phone_id": "527693490",
        "date": "19/03/2026",
        "course": "מו\"ץ בהלכות שבת",
        "city": "ירושלים",
        "recording_url": "https://drive.google.com/file/d/1OCxH_BjNJ94n_ouQEvo1i4d9jmTlf4jo/preview",
        "message": "אז יום טוב, היי.\nשעות קשר, אני לא כל כך מבין.\nבאיזה שעות זה?\nומה צריך לעשות? אם יש שעות\nשמי שיתקשר אליי,\n052 769 3490.\nעוד הפעם, 052 769 3490. אני מאוד אשמח שיתקשרו אליי. תודה, הצלחה."
    },
    {
        "phone_id": "504198890",
        "date": "19/03/2026",
        "course": "מו\"ץ בהלכות שבת", 
        "city": "ביתר",
        "recording_url": "https://drive.google.com/file/d/10drKQ_a7b7rYhInlGE6Hfeivu4pZh0ba/preview",
        "message": "איתי גלצמן, נרשם על ידי חוי שבת, ביתר, 0504198890"
    },
    {
        "phone_id": "527694567",
        "date": "19/03/2026",
        "course": "מו\"ץ בהלכות שבת",
        "city": "בית שמש",
        "recording_url": "https://drive.google.com/file/d/1gfjHuz390UhJnvZKPPL4zq28jQpWL1FA/preview",
        "message": "אבי כהן, צ'ק ליזר, גוסטב רייך."
    }
]

def extract_name_from_message(message: str) -> Optional[str]:
    """Extract name from message if present."""
    if not message:
        return None
    
    lines = message.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Look for patterns like "שמי X" or just names at start of line
        if line.startswith('שמי '):
            return line.replace('שמי ', '').strip()
        elif ',' in line and len(line.split()) <= 4 and not any(word in line for word in ['תודה', 'רחוב', 'מספר']):
            # Likely a name line
            return line.split(',')[0].strip()
    return None

def extract_phone_from_message(message: str) -> Optional[str]:
    """Extract phone number from message if present."""
    if not message:
        return None
    
    import re
    # Look for phone patterns like 05x-xxxxxxx or 05x xxxxxxx
    phone_pattern = r'0(5[0-9])-?\d{7}|0(5[0-9])\d{7}'
    match = re.search(phone_pattern, message)
    if match:
        phone = match.group()
        return phone.replace('-', '')
    return None

async def import_leads(dry_run: bool = False):
    """Import Nissan telemarketing leads."""
    async with SessionLocal() as session:
        created_count = 0
        skipped_count = 0
        duplicate_count = 0
        
        for lead_data in LEADS_DATA:
            phone = lead_data["phone_id"]
            
            # Check if lead already exists
            existing = await session.execute(
                select(Lead).where(Lead.phone == phone)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Lead with phone {phone} already exists - skipping")
                skipped_count += 1
                continue
            
            # Extract name and phone from message
            name = extract_name_from_message(lead_data["message"])
            extracted_phone = extract_phone_from_message(lead_data["message"])
            
            # Use extracted phone if different and more complete
            if extracted_phone and len(extracted_phone) > len(phone):
                phone = extracted_phone
            
            # Check again with updated phone
            existing = await session.execute(
                select(Lead).where(Lead.phone == phone)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Lead with extracted phone {phone} already exists - skipping")
                skipped_count += 1
                continue
            
            # Parse date
            try:
                arrival_date = datetime.strptime(lead_data["date"], "%d/%m/%Y")
            except ValueError:
                arrival_date = datetime.now()
            
            # Create lead
            lead = Lead(
                full_name=name or f"ליד מצינתוק ניסן ({phone})",
                phone=phone,
                city=lead_data["city"],
                source_type="טלמרקטינג",
                source_name="צינתוק ניסן",
                source_message=lead_data["message"],
                source_details=f"קורס: {lead_data['course']}\nהקלטה: {lead_data['recording_url']}",
                requested_course=lead_data["course"],
                arrival_date=arrival_date,
                status="ליד חדש",
                created_at=datetime.now()
            )
            
            if not dry_run:
                try:
                    session.add(lead)
                    await session.commit()
                    logger.info(f"Created lead: {lead.full_name} ({lead.phone})")
                    created_count += 1
                except Exception as e:
                    await session.rollback()
                    if "duplicate key" in str(e) or "already exists" in str(e):
                        logger.warning(f"Duplicate phone {phone} - skipping")
                        duplicate_count += 1
                    else:
                        logger.error(f"Error creating lead for {phone}: {e}")
                        raise
            else:
                logger.info(f"[DRY RUN] Would create lead: {lead.full_name} ({lead.phone})")
                created_count += 1
        
        logger.info(f"Import complete: {created_count} leads created, {skipped_count} skipped, {duplicate_count} duplicates")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Import Nissan telemarketing leads")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without actually doing it")
    args = parser.parse_args()
    
    asyncio.run(import_leads(dry_run=args.dry_run))

if __name__ == "__main__":
    main()
