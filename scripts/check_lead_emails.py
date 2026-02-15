"""
Check emails for a specific lead
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from db import SessionLocal
from db.models import InboundEmail, Lead


async def check_lead():
    async with SessionLocal() as db:
        # Find lead by email
        stmt = select(Lead).where(Lead.email == 'stalasher@gmail.com')
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            print("❌ Lead not found with email: stalasher@gmail.com")
            return

        print(f"✅ Found Lead #{lead.id}: {lead.full_name}")
        print(f"   Email: {lead.email}")
        print("=" * 60)

        # Find emails for this lead
        stmt = select(InboundEmail).where(InboundEmail.lead_id == lead.id).order_by(InboundEmail.id)
        result = await db.execute(stmt)
        emails = result.scalars().all()

        print(f"\n📧 Found {len(emails)} emails for this lead:")
        print("=" * 60)

        for email in emails:
            print(f"\nEmail #{email.id}:")
            print(f"  Direction: {email.direction}")
            print(f"  From: {email.from_email}")
            print(f"  Subject: {email.subject}")
            print(f"  Date: {email.email_date}")
            print(f"  Lead ID: {email.lead_id}")
            print(f"  Matched Auto: {email.matched_auto}")

        # Also check emails where from_email matches
        print("\n" + "=" * 60)
        print("📧 Checking emails where from_email = stalasher@gmail.com:")
        print("=" * 60)

        stmt = select(InboundEmail).where(InboundEmail.from_email == 'stalasher@gmail.com').order_by(InboundEmail.id)
        result = await db.execute(stmt)
        matching_emails = result.scalars().all()

        print(f"\nFound {len(matching_emails)} emails from stalasher@gmail.com:")
        for email in matching_emails:
            print(f"\nEmail #{email.id}:")
            print(f"  Direction: {email.direction}")
            print(f"  Subject: {email.subject}")
            print(f"  Lead ID: {email.lead_id} (should be {lead.id})")
            print(f"  Matched Auto: {email.matched_auto}")


if __name__ == "__main__":
    asyncio.run(check_lead())
