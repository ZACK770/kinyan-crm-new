import asyncio
import os

import asyncpg


SUSPECT_TABLES = [
    "tenants",
    "tenant_settings",
    "donations",
    "contacts",
    "standing_orders",
    "donation_products",
    "donation_purposes",
    "cashflow_entries",
    "cashflow_limits",
    "bank_transfers",
]


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise SystemExit("DATABASE_URL is not set")

    url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

    conn = await asyncpg.connect(url, ssl="require")
    try:
        db = await conn.fetchval("select current_database()")
        usr = await conn.fetchval("select current_user")
        ver = await conn.fetchval("select version()")
        rows = await conn.fetch(
            """
            select table_name
            from information_schema.tables
            where table_schema='public'
              and table_type='BASE TABLE'
            order by table_name
            """
        )
        names = [r["table_name"] for r in rows]
        suspects = [t for t in SUSPECT_TABLES if t in names]

        print("current_database:", db)
        print("current_user:", usr)
        print("version:", ver.splitlines()[0])
        print("suspect_tables_present:", suspects)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
