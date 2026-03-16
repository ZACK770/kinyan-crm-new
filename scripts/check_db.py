import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

async def check():
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        # Last audit logs to see when system was last active
        print("=== LAST AUDIT LOGS (last 10) ===")
        r = await conn.execute(text(
            "SELECT id, action, entity_type, description, created_at "
            "FROM audit_logs ORDER BY created_at DESC LIMIT 10"
        ))
        for row in r.fetchall():
            print(f"  {row}")

        # Last lead interactions
        print("\n=== LAST LEAD INTERACTIONS (last 5) ===")
        r = await conn.execute(text(
            "SELECT id, lead_id, interaction_type, created_at "
            "FROM lead_interactions ORDER BY created_at DESC LIMIT 5"
        ))
        for row in r.fetchall():
            print(f"  {row}")

        # Last webhook logs to see last successful webhook
        print("\n=== LAST WEBHOOK LOGS (last 10) ===")
        r = await conn.execute(text(
            "SELECT id, source, status, created_at "
            "FROM webhook_logs ORDER BY created_at DESC LIMIT 10"
        ))
        for row in r.fetchall():
            print(f"  {row}")

    await engine.dispose()

asyncio.run(check())
