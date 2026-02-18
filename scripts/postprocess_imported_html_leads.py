"""Post-process leads imported from two HTML reports.

1) Assign a random salesperson to imported leads that currently have no salesperson.
   Excludes salespeople whose name contains "גרינהויז" or "ברים".

2) For the "קמפיין מימוש הטבה" report: set status to "לא רלוונטי" for leads whose
   *latest* campaign interaction indicates removal (i.e. not "רוצה פרטים מנציג").

Run without args for DRY RUN. Use --live to apply changes.
"""

import argparse
import asyncio
import random
from typing import Iterable

import asyncpg

DB_URL = "postgresql://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

SOURCE_CALLBACKS = "מספרים לחזרה - ימות המשיח"
SOURCE_CAMPAIGN = "קמפיין מימוש הטבה - ימות המשיח"

EXCLUDED_SALESPERSON_SUBSTRINGS = ["גרינהויז", "ברים"]


def _contains_any(text: str, subs: Iterable[str]) -> bool:
    t = (text or "").strip()
    return any(s in t for s in subs)


async def fetch_eligible_salespeople(conn: asyncpg.Connection) -> list[asyncpg.Record]:
    rows = await conn.fetch(
        """
        SELECT id, name
        FROM salespeople
        WHERE is_active = true
        ORDER BY id
        """
    )

    eligible: list[asyncpg.Record] = []
    for r in rows:
        if not _contains_any(r["name"], EXCLUDED_SALESPERSON_SUBSTRINGS):
            eligible.append(r)

    return eligible


async def assign_salespeople(conn: asyncpg.Connection, dry_run: bool) -> tuple[int, int]:
    """Returns (leads_without_salesperson, updated_count)."""

    leads = await conn.fetch(
        """
        SELECT id, phone, full_name, source_name
        FROM leads
        WHERE salesperson_id IS NULL
          AND source_name = ANY($1)
        ORDER BY id
        """,
        [SOURCE_CALLBACKS, SOURCE_CAMPAIGN],
    )

    eligible_salespeople = await fetch_eligible_salespeople(conn)
    if not eligible_salespeople:
        raise RuntimeError("No eligible active salespeople found (after exclusions)")

    updated = 0

    # Deterministic-ish random for reproducibility within a single run
    rng = random.Random(42)
    salesperson_ids = [r["id"] for r in eligible_salespeople]

    # Spread assignments randomly
    for lead in leads:
        sp_id = rng.choice(salesperson_ids)
        if not dry_run:
            await conn.execute(
                """
                UPDATE leads
                SET salesperson_id = $1,
                    updated_at = NOW()
                WHERE id = $2
                """,
                sp_id,
                lead["id"],
            )
        updated += 1

    return len(leads), updated


async def reassign_excluded_salespeople(conn: asyncpg.Connection, dry_run: bool) -> tuple[int, int]:
    """Reassign imported leads that are currently assigned to excluded salespeople.

    Returns (excluded_assigned_count, updated_count).
    """

    eligible_salespeople = await fetch_eligible_salespeople(conn)
    if not eligible_salespeople:
        raise RuntimeError("No eligible active salespeople found (after exclusions)")

    leads = await conn.fetch(
        """
        SELECT l.id, l.phone, l.full_name, sp.name AS salesperson_name
        FROM leads l
        JOIN salespeople sp ON sp.id = l.salesperson_id
        WHERE l.source_name = ANY($1)
          AND (
            sp.name ILIKE '%' || $2 || '%'
            OR sp.name ILIKE '%' || $3 || '%'
          )
        ORDER BY l.id
        """,
        [SOURCE_CALLBACKS, SOURCE_CAMPAIGN],
        EXCLUDED_SALESPERSON_SUBSTRINGS[0],
        EXCLUDED_SALESPERSON_SUBSTRINGS[1],
    )

    updated = 0
    rng = random.Random(43)
    salesperson_ids = [r["id"] for r in eligible_salespeople]

    for lead in leads:
        sp_id = rng.choice(salesperson_ids)
        if not dry_run:
            await conn.execute(
                """
                UPDATE leads
                SET salesperson_id = $1,
                    updated_at = NOW()
                WHERE id = $2
                """,
                sp_id,
                lead["id"],
            )
        updated += 1

    return len(leads), updated


async def mark_campaign_removals_not_relevant(conn: asyncpg.Connection, dry_run: bool) -> tuple[int, int]:
    """Returns (candidates_count, updated_count)."""

    # Pick latest campaign interaction per lead.
    rows = await conn.fetch(
        """
        WITH latest_campaign AS (
            SELECT
                li.lead_id,
                li.description,
                li.interaction_date,
                ROW_NUMBER() OVER (PARTITION BY li.lead_id ORDER BY li.interaction_date DESC, li.id DESC) AS rn
            FROM lead_interactions li
            JOIN leads l ON l.id = li.lead_id
            WHERE l.source_name = $1
              AND li.description LIKE 'חזר לקמפיין מימוש הטבה%'
        )
        SELECT lead_id, description, interaction_date
        FROM latest_campaign
        WHERE rn = 1
        """,
        SOURCE_CAMPAIGN,
    )

    # "לא ענו 1" == not "רוצה פרטים מנציג" in latest campaign interaction
    to_update: list[int] = []
    for r in rows:
        desc = r["description"] or ""
        if "רוצה פרטים מנציג" not in desc:
            to_update.append(r["lead_id"])

    if not dry_run and to_update:
        await conn.execute(
            """
            UPDATE leads
            SET status = 'לא רלוונטי',
                updated_at = NOW()
            WHERE id = ANY($1)
            """,
            to_update,
        )

    return len(rows), len(to_update)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    dry_run = not args.live

    print("=" * 80)
    print("Post-process imported HTML leads")
    print("=" * 80)
    print("Mode:", "DRY RUN" if dry_run else "LIVE")

    conn = await asyncpg.connect(DB_URL)
    try:
        # 1) Salespeople assignment
        missing_cnt, assigned_cnt = await assign_salespeople(conn, dry_run=dry_run)
        print("\nSalesperson assignment")
        print("- Leads without salesperson (imported only):", missing_cnt)
        print("- Would assign" if dry_run else "- Assigned", assigned_cnt)

        # 1b) Reassign excluded salespeople
        excluded_cnt, reassigned_cnt = await reassign_excluded_salespeople(conn, dry_run=dry_run)
        print("\nReassign excluded salespeople")
        print("- Imported leads currently assigned to excluded salespeople:", excluded_cnt)
        print("- Would reassign" if dry_run else "- Reassigned", reassigned_cnt)

        # 2) Campaign status update
        candidates_cnt, updated_cnt = await mark_campaign_removals_not_relevant(conn, dry_run=dry_run)
        print("\nCampaign status update")
        print("- Leads with campaign interaction found:", candidates_cnt)
        print("- Would set status=לא רלוונטי" if dry_run else "- Set status=לא רלוונטי", updated_cnt)

        if dry_run:
            print("\nTo apply changes: python scripts\\postprocess_imported_html_leads.py --live")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
