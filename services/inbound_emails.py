"""
Inbound Emails service.
Processes email webhooks from Make.com (Gmail sync) and manages inbound email records.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import InboundEmail, Lead

logger = logging.getLogger(__name__)


def _determine_direction(label_ids: list[str] | None, sys_folders: list[dict] | None) -> str:
    """Determine email direction from Gmail labels/folders."""
    if sys_folders:
        folder_ids = [f.get("id", "") for f in sys_folders]
        if "SENT" in folder_ids:
            return "outbound"
    if label_ids and "SENT" in label_ids:
        return "outbound"
    return "inbound"


def _determine_folder(label_ids: list[str] | None, sys_folders: list[dict] | None) -> str:
    """Determine primary folder from Gmail labels."""
    if sys_folders:
        folder_ids = [f.get("id", "") for f in sys_folders]
        if "SENT" in folder_ids:
            return "SENT"
        if "INBOX" in folder_ids:
            return "INBOX"
    if label_ids:
        if "SENT" in label_ids:
            return "SENT"
        if "INBOX" in label_ids:
            return "INBOX"
    return "OTHER"


def _parse_email_date(date_str: str | None) -> datetime | None:
    """Parse internalDate from Gmail webhook."""
    if not date_str:
        return None
    try:
        # ISO format: "2023-08-23T15:16:35.000Z"
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


async def _match_lead(db: AsyncSession, from_email: str, to_emails: list[dict], direction: str) -> tuple[int | None, bool]:
    """
    Try to auto-match an email to a lead.
    For outbound: match by to_email
    For inbound: match by from_email
    Returns (lead_id, matched_auto)
    """
    emails_to_search = []
    
    if direction == "inbound":
        # For inbound emails, match by sender (from_email)
        if from_email:
            emails_to_search.append(from_email.lower())
    else:
        # For outbound emails, match by recipients (to_emails)
        for to in to_emails:
            email = to.get("email", "").lower()
            if email:
                emails_to_search.append(email)

    if not emails_to_search:
        return None, False

    stmt = select(Lead).where(
        func.lower(Lead.email).in_(emails_to_search)
    ).limit(1)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    if lead:
        return lead.id, True
    return None, False


async def process_email_batch(
    db: AsyncSession,
    emails: list[dict],
) -> dict:
    """
    Process a batch of emails from Make.com webhook.
    Returns summary of processing results.
    """
    created = 0
    skipped = 0
    errors = 0

    for email_data in emails:
        try:
            gmail_id = email_data.get("id")
            if not gmail_id:
                errors += 1
                continue

            # Check for duplicate
            existing = await db.execute(
                select(InboundEmail.id).where(InboundEmail.gmail_id == gmail_id)
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                continue

            # Parse fields
            label_ids = email_data.get("labelIds", [])
            sys_folders = email_data.get("sysFolders", [])
            direction = _determine_direction(label_ids, sys_folders)
            folder = _determine_folder(label_ids, sys_folders)

            from_email = email_data.get("fromEmail", "")
            from_name = email_data.get("fromName", "")
            to_list = email_data.get("to", [])
            bcc_list = email_data.get("bcc", [])

            headers = email_data.get("headers", {})
            message_id_header = headers.get("Message-ID", "")
            in_reply_to = headers.get("In-Reply-To", "")

            email_date = _parse_email_date(email_data.get("internalDate"))

            # Auto-match to lead
            lead_id, matched_auto = await _match_lead(db, from_email, to_list, direction)

            record = InboundEmail(
                gmail_id=gmail_id,
                thread_id=email_data.get("threadId"),
                direction=direction,
                from_email=from_email,
                from_name=from_name,
                to_emails=json.dumps(to_list, ensure_ascii=False) if to_list else None,
                bcc_emails=json.dumps(bcc_list, ensure_ascii=False) if bcc_list else None,
                subject=email_data.get("subject"),
                snippet=email_data.get("snippet"),
                body_text=email_data.get("fullTextBody"),
                body_html=email_data.get("htmlBody"),
                has_attachment=email_data.get("hasAttachment", False),
                attachments_count=email_data.get("attachmentsCount", 0),
                label_ids=json.dumps(label_ids, ensure_ascii=False) if label_ids else None,
                folder=folder,
                message_id_header=message_id_header or None,
                in_reply_to=in_reply_to or None,
                size_estimate=email_data.get("sizeEstimate"),
                history_id=email_data.get("historyId"),
                lead_id=lead_id,
                matched_auto=matched_auto,
                is_read=direction == "outbound",  # Outbound emails are auto-read
                email_date=email_date,
            )
            db.add(record)
            created += 1

        except Exception as e:
            logger.error(f"Error processing email {email_data.get('id', '?')}: {e}")
            errors += 1

    if created > 0:
        await db.flush()

    return {"created": created, "skipped": skipped, "errors": errors}


async def list_emails(
    db: AsyncSession,
    direction: str | None = None,
    folder: str | None = None,
    lead_id: int | None = None,
    is_read: bool | None = None,
    unmatched_only: bool = False,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[InboundEmail], int]:
    """List inbound emails with filters. Returns (items, total_count)."""
    base = select(InboundEmail)
    count_base = select(func.count()).select_from(InboundEmail)

    conditions = []
    if direction:
        conditions.append(InboundEmail.direction == direction)
    if folder:
        conditions.append(InboundEmail.folder == folder)
    if lead_id is not None:
        conditions.append(InboundEmail.lead_id == lead_id)
    if is_read is not None:
        conditions.append(InboundEmail.is_read == is_read)
    if unmatched_only:
        conditions.append(InboundEmail.lead_id.is_(None))
    if search:
        search_term = f"%{search}%"
        conditions.append(or_(
            InboundEmail.subject.ilike(search_term),
            InboundEmail.from_email.ilike(search_term),
            InboundEmail.from_name.ilike(search_term),
            InboundEmail.snippet.ilike(search_term),
        ))

    for cond in conditions:
        base = base.where(cond)
        count_base = count_base.where(cond)

    total = (await db.execute(count_base)).scalar() or 0

    stmt = base.order_by(InboundEmail.email_date.desc().nullslast()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def get_email(db: AsyncSession, email_id: int) -> InboundEmail | None:
    """Get a single email by ID."""
    result = await db.execute(select(InboundEmail).where(InboundEmail.id == email_id))
    return result.scalar_one_or_none()


async def get_thread(db: AsyncSession, thread_id: str) -> list[InboundEmail]:
    """Get all emails in a thread, ordered by date."""
    stmt = (
        select(InboundEmail)
        .where(InboundEmail.thread_id == thread_id)
        .order_by(InboundEmail.email_date.asc().nullslast())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def assign_lead(db: AsyncSession, email_id: int, lead_id: int | None) -> InboundEmail | None:
    """Assign or unassign a lead to an email."""
    email = await get_email(db, email_id)
    if not email:
        return None
    email.lead_id = lead_id
    email.matched_auto = False
    await db.flush()
    return email


async def mark_read(db: AsyncSession, email_id: int, read: bool = True) -> InboundEmail | None:
    """Mark an email as read/unread."""
    email = await get_email(db, email_id)
    if not email:
        return None
    email.is_read = read
    await db.flush()
    return email


async def get_unread_count(db: AsyncSession) -> int:
    """Get count of unread inbound emails."""
    stmt = (
        select(func.count())
        .select_from(InboundEmail)
        .where(InboundEmail.is_read == False)  # noqa: E712
        .where(InboundEmail.direction == "inbound")
    )
    return (await db.execute(stmt)).scalar() or 0
