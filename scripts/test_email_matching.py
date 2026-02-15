"""
Test Email Matching on Small Sample
Tests the matching logic on first 20 emails to see if it works correctly.
"""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db import SessionLocal
from db.models import InboundEmail, Lead


async def match_email_to_lead(db: AsyncSession, email: InboundEmail) -> tuple[int | None, str]:
    """
    Try to match an email to a lead.
    Returns (lead_id, reason)
    """
    # Parse to_emails if it's JSON
    to_emails_list = []
    if email.to_emails:
        try:
            to_emails_list = json.loads(email.to_emails)
        except (json.JSONDecodeError, TypeError):
            pass

    # Collect all email addresses to search
    emails_to_search = []
    
    # Always add from_email
    if email.from_email:
        emails_to_search.append(email.from_email.lower())
    
    # Add to_emails
    for to in to_emails_list:
        if isinstance(to, dict):
            email_addr = to.get("email", "").lower()
            if email_addr:
                emails_to_search.append(email_addr)

    if not emails_to_search:
        return None, "No email addresses to search"

    # Search for lead
    stmt = select(Lead).where(
        func.lower(Lead.email).in_(emails_to_search)
    ).limit(1)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    if lead:
        # Figure out which email matched
        matched_email = None
        if lead.email.lower() == email.from_email.lower():
            matched_email = f"from: {email.from_email}"
        else:
            for to in to_emails_list:
                if isinstance(to, dict) and to.get("email", "").lower() == lead.email.lower():
                    matched_email = f"to: {to.get('email')}"
                    break
        
        return lead.id, f"Matched via {matched_email} → Lead {lead.id} ({lead.full_name})"
    
    return None, f"No match found (searched: {', '.join(emails_to_search[:3])})"


async def test_matching():
    """
    Test matching on first 20 emails.
    """
    async with SessionLocal() as db:
        # Get first 20 emails
        stmt = select(InboundEmail).order_by(InboundEmail.id).limit(20)
        result = await db.execute(stmt)
        emails = result.scalars().all()

        print(f"🧪 Testing email matching on {len(emails)} emails")
        print("=" * 80)

        for email in emails:
            # Parse to_emails for display
            to_display = "N/A"
            if email.to_emails:
                try:
                    to_list = json.loads(email.to_emails)
                    if to_list:
                        to_display = to_list[0].get("email", "N/A") if isinstance(to_list[0], dict) else str(to_list[0])
                except:
                    pass

            print(f"\n📧 Email #{email.id}")
            print(f"   Direction: {email.direction}")
            print(f"   From: {email.from_email}")
            print(f"   To: {to_display}")
            print(f"   Subject: {email.subject[:50] if email.subject else 'N/A'}")
            print(f"   Current lead_id: {email.lead_id}")
            
            # Try to match
            lead_id, reason = await match_email_to_lead(db, email)
            
            if lead_id:
                if lead_id == email.lead_id:
                    print(f"   ✅ {reason} (already correct)")
                else:
                    print(f"   🔄 {reason} (would change from {email.lead_id})")
            else:
                print(f"   ❌ {reason}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    print("🧪 Testing email-to-lead matching logic...\n")
    asyncio.run(test_matching())
    print("\n✅ Test complete!")
