import asyncio
import asyncpg

async def check_leads_schema():
    conn = await asyncpg.connect(
        host="dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com",
        port=5432,
        database="crm_new",
        user="crm_new_user",
        password="45RsFRWnUuvPQFAttG37PxisVlC79HZv"
    )
    
    try:
        # Get column info for leads table
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'leads' AND column_name = 'created_at'
        """)
        
        for row in result:
            print(f"Column: {row['column_name']}")
            print(f"Type: {row['data_type']}")
            print(f"Nullable: {row['is_nullable']}")
            print(f"Default: {row['column_default']}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_leads_schema())
