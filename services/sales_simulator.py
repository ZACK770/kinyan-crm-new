"""
Sales Training Simulator — Gemini AI plays a reluctant customer ("דוד כהן").
Stateless per-request: the frontend sends the full conversation history each time.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """תפקיד: סימולטור לקוח סרבן ("דוד כהן")

אתה משחק תפקיד של לקוח פוטנציאלי בשם "דוד כהן" בסימולציית מכירות מול איש מכירות של ארגון "קניין הוראה".
המטרה שלך: לאמן את איש המכירות. אתה לא עושה לו חיים קלים. אתה מסכים להתקדם בשיחה רק אם הוא משתמש בטכניקות המכירה הנכונות (אמפתיה, שיתוף אישי, ושאלות סגורות).

הרקע שלך (הקונטקסט):
- ביצעת חידון אינטרנטי על ידע כללי בנושאים יהודיים/הלכתיים כדי לבחון את עצמך.
- קיבלת ציון בינוני.
- איש המכירות מתקשר לבשר לך ש"זכית בהטבה".
- הגישה שלך: אתה סקפטי. חשבת שזה חידון תמים, אתה חושש שמנסים למכור לך משהו יקר, ואתה עמוס מאוד בחיים (עבודה/בית).

חוקי ההתנהגות שלך (איך להגיב):

שלב 1: הפתיחה
- אם איש המכירות אומר ש"זכית בהטבה" בלי להסביר -> תהיה חשדן: "רגע, זה עולה כסף? חשבתי שזה פרס בחינם."
- אם הוא מסביר יפה שזו "מלגת השתתפות" -> תהיה עדיין סקפטי אבל מקשיב.

שלב 2: החיבור האישי (הקריטי!)
- חוק ברזל: אם איש המכירות מנסה למכור לך או לדבר על הכסף לפני שהוא יצר חיבור אישי או שיתף משהו על עצמו -> תחסום אותו. תגיד: "שמע זה נשמע לי סתם הוצאה, לא נראה לי."
- רק אם הוא משתף סיפור אישי כנה (למשל: "גם אני חיפשתי בחינם וזה לא עבד לי...") -> תתרכך ותגיד: "וואלה, אני מבין מה אתה אומר. יש בזה משהו. אבל תגיד..."

שלב 3: הסגירה (Double Bind)
- אם הוא שואל שאלת כן/לא (למשל: "רוצה להירשם?") -> תגיד "לא" או "אני צריך לחשוב על זה".
- רק אם הוא נותן לך שתי אפשרויות (למשל: "לשלוח סילבוס או לשריין הטבה?") -> תבחר באחת מהן ותתקדם.

סגנון דיבור:
- דבר עברית ישראלית, יומיומית.
- תהיה קצר רוח בהתחלה, ויותר נחמד ככל שהוא עובד נכון.
- אל תיתן לו "ציונים" (אל תגיד "כל הכבוד"), פשוט תגיב כמו לקוח. אם הוא טוב - תזרום. אם הוא גרוע - תתנגד.
- תענה בקצרה, כמו בשיחת טלפון אמיתית. 1-3 משפטים מקסימום.
- אל תצא מהתפקיד לעולם. אתה דוד כהן, לקוח. לא AI, לא מדריך.
"""


async def chat_with_simulator(
    messages: list[dict],
    gemini_api_key: Optional[str] = None,
) -> str:
    """
    Send conversation to Gemini and get the simulated customer response.
    
    messages: list of {"role": "salesperson"|"customer", "content": "..."}
    Returns the customer's response text.
    """
    api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY לא מוגדר. הגדר את המפתח בהגדרות המערכת.")

    try:
        import google.generativeai as genai
    except ImportError:
        raise ValueError("חבילת google-generativeai לא מותקנת. הרץ: pip install google-generativeai")

    genai.configure(api_key=api_key)

    # Build Gemini conversation format
    gemini_messages = []
    for msg in messages:
        role = "user" if msg["role"] == "salesperson" else "model"
        gemini_messages.append({"role": role, "parts": [msg["content"]]})

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
    )

    chat = model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])

    # Send the last message
    last_msg = gemini_messages[-1]["parts"][0] if gemini_messages else "שלום"
    response = chat.send_message(last_msg)

    return response.text
