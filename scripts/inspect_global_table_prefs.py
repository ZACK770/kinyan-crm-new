import asyncio
import os

import asyncpg


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise SystemExit("DATABASE_URL is not set")

    url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

    conn = await asyncpg.connect(url, ssl="require")
    try:
        print("== indexes ==")
        rows = await conn.fetch(
            """
            select indexname, indexdef
            from pg_indexes
            where schemaname='public'
              and tablename='global_table_prefs'
            order by indexname
            """
        )
        for r in rows:
            print(r["indexname"], ":", r["indexdef"])

        print("\n== constraints ==")
        rows = await conn.fetch(
            """
            select conname, contype, pg_get_constraintdef(oid) as def
            from pg_constraint
            where conrelid = 'public.global_table_prefs'::regclass
            order by conname
            """
        )
        for r in rows:
            print(r["conname"], r["contype"], ":", r["def"])
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
