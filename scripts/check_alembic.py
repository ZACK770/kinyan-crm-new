"""Reset alembic_version so we can start fresh."""
import asyncio
import os
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new'

async def reset():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.begin() as conn:
        r = await conn.execute(text("SELECT version_num FROM alembic_version"))
        rows = r.fetchall()
        print(f"Before: {[row[0] for row in rows]}")
        await conn.execute(text("DELETE FROM alembic_version"))
        print("Cleared alembic_version table")
    await engine.dispose()

asyncio.run(reset())
