import asyncio
from sqlalchemy import select
from db import get_db
from db.models import Lead, Salesperson
import os

async def test_update():
    print("🚀 Starting Lead Update Test Script")
    async for db in get_db():
        # 1. Get a lead to test with
        stmt = select(Lead).limit(1)
        result = await db.execute(stmt)
        lead = result.scalar()
        
        if not lead:
            print("❌ No leads found in database")
            return

        original_status = lead.status
        original_sp_id = lead.salesperson_id
        lead_id = lead.id
        
        print(f"📍 Testing with Lead ID: {lead_id}")
        print(f"   Original Status: '{original_status}'")
        print(f"   Original SP_ID: {original_sp_id}")

        # 2. Try to update status
        from services.leads import update_lead
        new_status = "במעקב" if original_status != "במעקב" else "ליד חדש"
        
        print(f"🔄 Attempting to update status to: '{new_status}'")
        updated_lead = await update_lead(db, lead_id, status=new_status)
        
        if updated_lead:
            await db.commit()
            print("✅ Status update committed")
            
            # 3. Verify from DB
            await db.refresh(updated_lead)
            print(f"📊 Verified Status in DB: '{updated_lead.status}'")
            
            if updated_lead.status == new_status:
                print("✨ SUCCESS: Status updated correctly in DB")
            else:
                print("❌ FAILURE: Status in DB does not match expected value")
        else:
            print("❌ FAILURE: update_lead returned None")
        
        break

if __name__ == "__main__":
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
    asyncio.run(test_update())
