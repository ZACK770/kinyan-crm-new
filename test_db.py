import asyncio
import asyncpg

async def test():
    try:
        print("Trying to connect to Render PostgreSQL...")
        conn = await asyncio.wait_for(
            asyncpg.connect('postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new'),
            timeout=10
        )
        print('Connected successfully!')
        result = await conn.fetchval('SELECT 1')
        print(f'Query result: {result}')
        await conn.close()
    except asyncio.TimeoutError:
        print('ERROR: Connection timed out after 10 seconds')
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}')

if __name__ == "__main__":
    asyncio.run(test())
