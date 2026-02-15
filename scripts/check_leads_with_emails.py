"""
Check how many leads have email addresses
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from db import SessionLocal
from db.models import Lead


async def check_leads():
    async with SessionLocal() as db:
        # Total leads
        total = await db.execute(select(func.count(Lead.id)))
        total_count = total.scalar()

        # Leads with email
        with_email = await db.execute(
            select(func.count(Lead.id)).where(Lead.email.isnot(None)).where(Lead.email != '')
        )
        with_email_count = with_email.scalar()

        # Sample of leads with emails
        stmt = select(Lead).where(Lead.email.isnot(None)).where(Lead.email != '').limit(10)
        result = await db.execute(stmt)
        sample_leads = result.scalars().all()

        print("=" * 60)
        print(f"📊 Leads Statistics:")
        print(f"   Total leads: {total_count}")
        print(f"   Leads with email: {with_email_count} ({with_email_count/total_count*100:.1f}%)")
        print(f"   Leads without email: {total_count - with_email_count}")
        print("=" * 60)
        print(f"\n📧 Sample of 10 leads with emails:")
        for lead in sample_leads:
            print(f"   Lead {lead.id}: {lead.full_name} - {lead.email}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_leads())
