"""
Sales Training Simulator — Gemini AI plays DUAL ROLE:
  1. "David Cohen" — reluctant customer
  2. Sales Mentor — gives feedback to the trainee

Returns structured JSON per turn: customer_reply, mentor_feedback, sentiment, is_closed.
Stateless per-request: the frontend sends the full conversation history each time.
"""
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a dual-role AI for a sales training simulator.

ROLE 1: "David Cohen" (The Customer)
- Context: You took a quiz about "Shabbat Laws", got a mediocre score.
- Event: Sales rep contacts you to say you "won a benefit" (discount) for a course by "קניין הוראה".
- Personality: Skeptical, busy, honest Israeli. Speaks informal Hebrew.
- Triggers (Negative):
  1. If they mention money/price before building rapport/trust -> You reject ("נשמע יקר, לא מתאים").
  2. If they say "It's free" when it's not -> You get suspicious.
  3. If they ask Yes/No questions (e.g., "Want to sign up?") -> You say No or "I need to think".
- Triggers (Positive):
  1. If they validate your skepticism ("I understand why you ask") -> You listen.
  2. If they share a PERSONAL story ("I also struggled with Shabbat laws...") -> You trust them.
  3. If they use DOUBLE BIND closing ("Send syllabus OR sign up now?") -> You choose one.
- Style: Short replies (1-3 sentences), casual Israeli Hebrew. Never break character.

ROLE 2: "The Mentor" (Sales Coach)
- Analyze the user's (Sales Rep) last message.
- Did they show empathy? Did they use the "Double Bind" technique? Did they bridge the "free vs paid" gap correctly?
- Provide short, constructive feedback in Hebrew. Be specific about what was good or what to improve.

OUTPUT FORMAT: JSON ONLY. No markdown, no code fences, just raw JSON.
{
  "customer_reply": "String (David's reply in Hebrew)",
  "mentor_feedback": "String (Coach's tip in Hebrew)",
  "sentiment": "positive" | "neutral" | "negative",
  "is_closed": boolean (true if sale is successfully closed)
}
"""


async def chat_with_simulator(
    messages: list[dict],
    gemini_api_key: Optional[str] = None,
) -> dict:
    """
    Send conversation to Gemini and get structured response.

    messages: list of {"role": "salesperson"|"customer", "content": "..."}
    Returns dict with customer_reply, mentor_feedback, sentiment, is_closed.
    """
    api_key = (gemini_api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
    if not api_key:
        all_keys = [k for k in os.environ.keys() if "GEMINI" in k.upper()]
        logger.error(f"GEMINI_API_KEY not found. Env vars with GEMINI: {all_keys}")
        raise ValueError("GEMINI_API_KEY לא מוגדר. הגדר את המפתח בהגדרות המערכת.")

    try:
        import google.generativeai as genai
    except ImportError:
        raise ValueError("חבילת google-generativeai לא מותקנת. הרץ: pip install google-generativeai")

    genai.configure(api_key=api_key)

    # Build Gemini conversation history
    # First message is the system prompt context, then alternating user/model
    gemini_history = []
    for msg in messages[:-1]:  # all except last
        role = "user" if msg["role"] == "salesperson" else "model"
        content = f'Sales Rep says: "{msg["content"]}"' if msg["role"] == "salesperson" else msg["content"]
        gemini_history.append({"role": role, "parts": [content]})

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config={"response_mime_type": "application/json"},
    )

    chat = model.start_chat(history=gemini_history)

    # Send the last message
    last_msg = messages[-1]
    last_text = f'Sales Rep says: "{last_msg["content"]}"' if last_msg["role"] == "salesperson" else last_msg["content"]
    response = chat.send_message(last_text)

    # Parse JSON response
    raw = response.text.strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(f"Gemini returned non-JSON: {raw[:200]}")
        # Fallback: treat as plain customer reply
        parsed = {
            "customer_reply": raw,
            "mentor_feedback": "",
            "sentiment": "neutral",
            "is_closed": False,
        }

    # Ensure all required fields
    return {
        "customer_reply": parsed.get("customer_reply", raw),
        "mentor_feedback": parsed.get("mentor_feedback", ""),
        "sentiment": parsed.get("sentiment", "neutral"),
        "is_closed": bool(parsed.get("is_closed", False)),
    }
