"""
Seed the 'קורס שבת' email template with text + PDF attachments from presentation/shabat/
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from db import SessionLocal
from db.models import EmailTemplate, File

TEMPLATE_NAME = "ערכת התרשמות - קורס שבת"
TEMPLATE_SUBJECT = "הזמנה ללימוד הלכה בשיטת קניין הוראה – קורס שבת"

TEMPLATE_BODY = """\
<div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.8; color: #333;">

<p style="font-size: 18px; font-weight: bold; color: #1a365d;">אלף נכנסים - להוראה!</p>

<p>כך תצאו עטורים בנזר הוראה, ובידיעת ההלכות:</p>

<ol style="font-size: 15px; font-weight: bold; color: #2c5282;">
  <li>הכנה!</li>
  <li>לימוד!</li>
  <li>סיכום!</li>
</ol>

<p>בשיטת הלימוד של קניין הוראה, תצטרפו לאלפים שהצליחו בזכות השיטה המוכחת:</p>

<h3 style="color: #2c5282;">הצעד הראשון:</h3>
<p>הכנה תמציתית מדויקת של הסוגיות והדעות המרכיבות את הסוגיה.<br>
הבהירות של הרב מוסר השיעור, החדות של המצגות, וחוברת העזר הבהירה – הופכות את הלימוד למתוק וקל במיוחד!</p>

<h3 style="color: #2c5282;">הצעד השני:</h3>
<p>לימוד השו"ע ונושאי כליו, מתוך ספר בהיר ומאיר עיניים בהוצאה מיוחדת של 'קניין הוראה'.<br>
הספר המוגה והערוך, סיכומי הסעיפים והמפתחות – מאפשרים לימוד מהיר, ושינון קל.</p>

<h3 style="color: #2c5282;">הצעד השלישי:</h3>
<p>סיכום הסוגיה, וההלכות למעשה. הסיכומים המפורטים, המלווים בהדמיות והמחשות.</p>

<p>זהו העקרון שיצר את מערך הלימוד של קניין הוראה: ערכת לימוד מושקעת ומהודרת, שיעורים מפי רבנים מופלגי תורה והלכה, ושקו"ט ומבחנים מעת לעת.</p>

<p style="font-weight: bold; color: #2c5282;">וזה לא הכול!</p>

<p>כדי להנעים ולחבב את שערי ציון – לימוד ההלכה – על הלומדים, משתתפי השיעורים זוכים גם לדיון הלכתי משותף, בו מנסים הם את כוחם בשו"ת בנוגע להלכה הנלמדת, כשמתק טעם התורה אינו מש מפיהם עד לשבוע הבא. השו"ת יוצאים בגליונות מהודרים מעת לעת עם שמות הכותבים.</p>

<p>בעוד שנה, כאשר משתתפי הקורס יסיימו את מסלול הלימודים בהצלחה, יזכו לעמוד בכור המבחן בבחינות 'קניין הוראה' ואצל גדולי הרבנים, ויזכו לתעודות וקנייני הוראה!</p>

<p style="font-size: 16px; font-weight: bold; color: #1a365d;">עכשיו. ההזמנות שלך!</p>

<p>מצורפים כאן טעימות מעזרי הלימוד, חוברות ההכנה והסיכומים, וסילבוס הלימודים במסלולים השונים.</p>

<p>בהצלחה!</p>

<p>בברכה,<br>
<strong>ישראל ברים</strong><br>
0527635459</p>

<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
<p style="color: #999; font-size: 12px;">
בברכה,<br>
קניין הוראה 5993*<br>
מספר ישיר למערך הלמידה הטלפוני: 03-3135124
</p>

</div>
"""

PDF_DIR = Path(__file__).parent.parent / "presentation" / "shabat"

async def seed():
    async with SessionLocal() as db:
        # Check if template already exists
        from sqlalchemy import select
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.name == TEMPLATE_NAME)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Template '{TEMPLATE_NAME}' already exists (id={existing.id}). Updating...")
            existing.subject = TEMPLATE_SUBJECT
            existing.body_html = TEMPLATE_BODY
            existing.category = "התרשמות"
            existing.track_type = "שבת"
            existing.is_active = True
            template_id = existing.id
        else:
            print(f"Creating template '{TEMPLATE_NAME}'...")
            template = EmailTemplate(
                name=TEMPLATE_NAME,
                subject=TEMPLATE_SUBJECT,
                body_html=TEMPLATE_BODY,
                category="התרשמות",
                track_type="שבת",
                is_active=True,
            )
            db.add(template)
            await db.flush()
            template_id = template.id
            print(f"  Created with id={template_id}")
        
        await db.commit()
        
        # Check existing attachments
        result = await db.execute(
            select(File).where(
                File.entity_type == "templates",
                File.entity_id == template_id
            )
        )
        existing_files = {f.filename for f in result.scalars().all()}
        
        # Upload PDF files one by one (large files need separate commits)
        pdf_files = sorted(PDF_DIR.glob("*.pdf"))
        print(f"\nFound {len(pdf_files)} PDF files in {PDF_DIR}")
        
        for pdf_path in pdf_files:
            if pdf_path.name in existing_files:
                print(f"  ⏭ {pdf_path.name} — already attached")
                continue
                
            data = pdf_path.read_bytes()
            size = len(data)
            print(f"  Uploading {pdf_path.name} ({size / (1024*1024):.1f} MB)...")
            
            file_record = File(
                filename=pdf_path.name,
                storage_key=None,  # DB storage
                file_data=data,
                content_type="application/pdf",
                size_bytes=size,
                entity_type="templates",
                entity_id=template_id,
                uploaded_by=None,
                is_public=False,
            )
            db.add(file_record)
            await db.commit()
            print(f"  ✅ {pdf_path.name}")
        
        print(f"\n✅ Done! Template '{TEMPLATE_NAME}' (id={template_id}) with {len(pdf_files)} attachments")

if __name__ == "__main__":
    asyncio.run(seed())
