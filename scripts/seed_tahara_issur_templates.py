"""
Seed email templates for 'קורס טהרה' and 'קורס איסור והיתר' (text only, files to be added later)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import select
from db import SessionLocal
from db.models import EmailTemplate

TEMPLATES = [
    {
        "name": "ערכת התרשמות - קורס טהרה",
        "subject": "הזמנה ללימוד הלכה בשיטת קניין הוראה – קורס טהרה",
        "category": "התרשמות",
        "track_type": "טהרה",
        "body_html": """\
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
""",
    },
    {
        "name": "ערכת התרשמות - קורס איסור והיתר",
        "subject": "הזמנה ללימוד הלכה בשיטת קניין הוראה – קורס איסור והיתר",
        "category": "התרשמות",
        "track_type": "איסור והיתר",
        "body_html": """\
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
""",
    },
]


async def seed():
    async with SessionLocal() as db:
        for tmpl in TEMPLATES:
            result = await db.execute(
                select(EmailTemplate).where(EmailTemplate.name == tmpl["name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Updating '{tmpl['name']}' (id={existing.id})...")
                existing.subject = tmpl["subject"]
                existing.body_html = tmpl["body_html"]
                existing.category = tmpl["category"]
                existing.track_type = tmpl["track_type"]
                existing.is_active = True
            else:
                print(f"Creating '{tmpl['name']}'...")
                template = EmailTemplate(
                    name=tmpl["name"],
                    subject=tmpl["subject"],
                    body_html=tmpl["body_html"],
                    category=tmpl["category"],
                    track_type=tmpl["track_type"],
                    is_active=True,
                )
                db.add(template)

            await db.commit()
            print(f"  ✅ Done")

    print("\n✅ All templates seeded (text only, no attachments yet)")


if __name__ == "__main__":
    asyncio.run(seed())
