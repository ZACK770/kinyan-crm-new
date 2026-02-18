import asyncio
import asyncpg

DB_URL = "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

SOURCE_CALLBACKS = "מספרים לחזרה - ימות המשיח"
SOURCE_CAMPAIGN = "קמפיין מימוש הטבה - ימות המשיח"

EXCL_1 = "גרינהויז"
EXCL_2 = "ברים"


async def main() -> None:
    conn = await asyncpg.connect(DB_URL)
    try:
        sources = [SOURCE_CALLBACKS, SOURCE_CAMPAIGN]

        rows = await conn.fetch(
            """
            SELECT sp.name, COUNT(*) AS cnt
            FROM leads l
            JOIN salespeople sp ON sp.id = l.salesperson_id
            WHERE l.source_name = ANY($1)
            GROUP BY sp.name
            ORDER BY cnt DESC
            """,
            sources,
        )

        print("Assigned leads by salesperson (imported sources):")
        for r in rows[:30]:
            print(f"- {r['name']}: {r['cnt']}")

        bad = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM leads l
            JOIN salespeople sp ON sp.id = l.salesperson_id
            WHERE l.source_name = ANY($1)
              AND (sp.name ILIKE '%' || $2 || '%' OR sp.name ILIKE '%' || $3 || '%')
            """,
            sources,
            EXCL_1,
            EXCL_2,
        )
        print(f"\nExcluded salespeople assigned count: {bad}")

        nr = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM leads l
            WHERE l.source_name = $1
              AND l.status = 'לא רלוונטי'
            """,
            SOURCE_CAMPAIGN,
        )
        print(f"Campaign leads with status לא רלוונטי: {nr}")

        no_sp = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM leads l
            WHERE l.source_name = ANY($1)
              AND l.salesperson_id IS NULL
            """,
            sources,
        )
        print(f"Imported leads still without salesperson_id: {no_sp}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
