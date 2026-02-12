import asyncio
from sqlalchemy import text
from db import engine

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='leads' AND column_name IN ('updated_at','last_edited_at','conversion_date') "
            "ORDER BY column_name"
        ))
        cols = [row[0] for row in r]
        print("Existing columns:", cols)
        missing = set(['updated_at', 'last_edited_at', 'conversion_date']) - set(cols)
        if missing:
            print("MISSING:", missing)
        else:
            print("All columns exist!")

asyncio.run(check())
