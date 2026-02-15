"""
Retroactive Email-to-Lead Matching Script
Matches existing inbound emails to leads based on email addresses.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from db import SessionLocal
from db.models import InboundEmail, Lead


async def match_email_to_lead(db: AsyncSession, email: InboundEmail) -> tuple[int | None, bool]:
    """
    Try to match an email to a lead based on direction.
    Returns (lead_id, matched)
    """
    emails_to_search = []
    
    if email.direction == "inbound":
        # For inbound emails, match by sender (from_email)
        if email.from_email:
            emails_to_search.append(email.from_email.lower())
    else:
        # For outbound emails, match by recipients (to_emails)
        if email.to_emails:
            import json
            try:
                to_list = json.loads(email.to_emails)
                for to in to_list:
                    if isinstance(to, dict):
                        email_addr = to.get("email", "").lower()
                        if email_addr:
                            emails_to_search.append(email_addr)
            except (json.JSONDecodeError, TypeError):
                pass

    if not emails_to_search:
        return None, False

    stmt = select(Lead).where(
        func.lower(Lead.email).in_(emails_to_search)
    ).limit(1)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    if lead:
        return lead.id, True
    return None, False


async def rematch_all_emails():
    """
    Go through all inbound emails and try to match them to leads.
    """
    async with SessionLocal() as db:
        # Get all emails (both matched and unmatched)
        stmt = select(InboundEmail).order_by(InboundEmail.id)
        result = await db.execute(stmt)
        all_emails = result.scalars().all()

        print(f"📧 Found {len(all_emails)} total emails in database")
        print("=" * 60)

        matched_count = 0
        unmatched_count = 0
        already_matched_count = 0
        newly_matched_count = 0
        unmatched_to_matched_count = 0

        for email in all_emails:
            was_matched = email.lead_id is not None
            lead_id, matched = await match_email_to_lead(db, email)
            
            if was_matched:
                already_matched_count += 1
                if lead_id != email.lead_id:
                    # Lead changed
                    print(f"🔄 Email {email.id} ({email.from_email}): Lead changed from {email.lead_id} to {lead_id}")
                    email.lead_id = lead_id
                    email.matched_auto = True
            else:
                # Was unmatched
                if lead_id:
                    # Now matched!
                    unmatched_to_matched_count += 1
                    print(f"✅ Email {email.id} ({email.from_email} → {email.direction}): Matched to Lead {lead_id}")
                    email.lead_id = lead_id
                    email.matched_auto = True
                else:
                    unmatched_count += 1

            if lead_id:
                matched_count += 1

        await db.commit()

        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   Total emails: {len(all_emails)}")
        print(f"   Already matched: {already_matched_count}")
        print(f"   Newly matched (was unmatched): {unmatched_to_matched_count}")
        print(f"   Still unmatched: {unmatched_count}")
        print(f"   Total matched now: {matched_count}")
        print("=" * 60)


if __name__ == "__main__":
    print("🔄 Starting retroactive email-to-lead matching...")
    print()
    asyncio.run(rematch_all_emails())
    print()
    print("✅ Done!")
