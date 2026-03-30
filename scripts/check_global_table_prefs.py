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
        exists = await conn.fetchval(
            """
            select exists (
                select 1
                from information_schema.tables
                where table_schema = 'public'
                  and table_name = 'global_table_prefs'
            )
            """
        )
        if not exists:
            print("global_table_prefs: table does not exist")
            return

        total = await conn.fetchval("select count(*) from global_table_prefs")
        distinct_cnt = await conn.fetchval("select count(distinct storage_key) from global_table_prefs")
        dup_cnt = await conn.fetchval(
            """
            select count(*) from (
                select storage_key
                from global_table_prefs
                group by storage_key
                having count(*) > 1
            ) t
            """
        )
        has_ix = await conn.fetchval(
            """
            select exists (
                select 1
                from pg_indexes
                where schemaname = 'public'
                  and tablename = 'global_table_prefs'
                  and indexname = 'ix_global_table_prefs_storage_key'
            )
            """
        )
        has_idx = await conn.fetchval(
            """
            select exists (
                select 1
                from pg_indexes
                where schemaname = 'public'
                  and tablename = 'global_table_prefs'
                  and indexname = 'idx_global_table_prefs_storage_key'
            )
            """
        )

        print("global_table_prefs.total_rows:", total)
        print("global_table_prefs.distinct_storage_keys:", distinct_cnt)
        print("global_table_prefs.duplicate_storage_keys_groups:", dup_cnt)
        print("index.ix_global_table_prefs_storage_key.exists:", has_ix)
        print("index.idx_global_table_prefs_storage_key.exists:", has_idx)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
