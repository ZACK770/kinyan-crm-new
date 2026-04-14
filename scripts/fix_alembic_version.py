import asyncio
import asyncpg

async def fix_alembic_version():
    conn = await asyncpg.connect(
        host="dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com",
        port=5432,
        database="crm_new",
        user="crm_new_user",
        password="45RsFRWnUuvPQFAttG37PxisVlC79HZv"
    )
    
    try:
        await conn.execute("UPDATE alembic_version SET version_num = '840f7bd52ad2'")
        print("✅ Fixed alembic_version table")
        
        # Verify the fix
        result = await conn.fetchval("SELECT version_num FROM alembic_version")
        print(f"Current version: {result}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_alembic_version())
