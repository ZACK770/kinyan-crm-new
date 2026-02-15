"""
Test Email Matching on Real User Emails
Find emails that are NOT from email@kinyanhoraah.co.il to test matching.
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from db import SessionLocal
from db.models import InboundEmail, Lead


async def test_real_emails():
    """
    Test matching on real user emails (not system emails).
    """
    async with SessionLocal() as db:
        # Get 30 emails that are NOT from email@kinyanhoraah.co.il
        stmt = (
            select(InboundEmail)
            .where(InboundEmail.from_email != 'email@kinyanhoraah.co.il')
            .where(InboundEmail.from_email != 'info@kinyanhoraah.co.il')
            .order_by(InboundEmail.id)
            .limit(30)
        )
        result = await db.execute(stmt)
        emails = result.scalars().all()

        print(f"🧪 Testing {len(emails)} real user emails")
        print("=" * 80)

        matched = 0
        unmatched = 0

        for email in emails:
            # Try to find lead by from_email
            stmt = select(Lead).where(func.lower(Lead.email) == email.from_email.lower()).limit(1)
            result = await db.execute(stmt)
            lead = result.scalar_one_or_none()

            status = "✅" if lead else "❌"
            if lead:
                matched += 1
            else:
                unmatched += 1

            print(f"{status} Email #{email.id}: {email.from_email[:40]:<40} → Lead: {lead.id if lead else 'None':<6} Current: {email.lead_id}")

        print("=" * 80)
        print(f"📊 Results: {matched} matched, {unmatched} unmatched")


if __name__ == "__main__":
    asyncio.run(test_real_emails())
