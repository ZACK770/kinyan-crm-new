from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, Salesperson, ChatThread, ChatThreadMember, ChatMessage, ChatMessageReadReceipt


async def _get_salesperson_ids_for_users(db: AsyncSession, user_ids: list[int]) -> dict[int, int]:
    if not user_ids:
        return {}
    result = await db.execute(
        select(Salesperson.user_id, Salesperson.id).where(Salesperson.user_id.in_(user_ids))
    )
    return {int(uid): int(sid) for (uid, sid) in result.all() if uid is not None and sid is not None}


async def list_threads_for_user(db: AsyncSession, user: User) -> list[ChatThread]:
    stmt = (
        select(ChatThread)
        .join(ChatThreadMember, ChatThreadMember.thread_id == ChatThread.id)
        .where(ChatThreadMember.user_id == user.id)
        .order_by(ChatThread.updated_at.desc().nullslast(), ChatThread.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def get_thread_for_user(db: AsyncSession, user: User, thread_id: int) -> Optional[ChatThread]:
    stmt = (
        select(ChatThread)
        .join(ChatThreadMember, ChatThreadMember.thread_id == ChatThread.id)
        .where(ChatThread.id == thread_id, ChatThreadMember.user_id == user.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_sales_team_thread(db: AsyncSession) -> ChatThread:
    stmt = select(ChatThread).where(ChatThread.is_sales_team == True)  # noqa: E712
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    thread = ChatThread(
        thread_type="group",
        title="כל אנשי המכירות",
        is_sales_team=True,
        created_at=func.now(),
        updated_at=func.now(),
    )
    db.add(thread)
    await db.flush()

    # Add all active salespeople (linked to users)
    sales_result = await db.execute(
        select(Salesperson).where(Salesperson.is_active == True, Salesperson.user_id.is_not(None))  # noqa: E712
    )
    salespeople = list(sales_result.scalars().all())
    members = [
        ChatThreadMember(thread_id=thread.id, user_id=int(sp.user_id))
        for sp in salespeople
        if sp.user_id is not None
    ]
    db.add_all(members)
    await db.flush()
    return thread


async def get_or_create_dm_thread(db: AsyncSession, user_a_id: int, user_b_id: int) -> ChatThread:
    # Find a dm thread that contains exactly these two users.
    # Implementation: find threads of type dm where both memberships exist.
    # (We don't enforce 'exactly 2' at query time; we ensure dm threads are always 2 users.)
    stmt = (
        select(ChatThread)
        .where(ChatThread.thread_type == "dm")
        .join(ChatThreadMember, ChatThreadMember.thread_id == ChatThread.id)
        .where(ChatThreadMember.user_id.in_([user_a_id, user_b_id]))
        .group_by(ChatThread.id)
        .having(func.count(func.distinct(ChatThreadMember.user_id)) == 2)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    thread = ChatThread(thread_type="dm", title=None, is_sales_team=False, created_at=func.now(), updated_at=func.now())
    db.add(thread)
    await db.flush()

    safe_ids = [uid for uid in [user_a_id, user_b_id] if uid and uid > 0]
    db.add_all([ChatThreadMember(thread_id=thread.id, user_id=uid) for uid in safe_ids])
    await db.flush()
    return thread


def _safe_user_id(user_id: int) -> int | None:
    """Convert fake dev user id (0) to None to avoid FK violations."""
    return user_id if user_id and user_id > 0 else None


async def create_group_thread(
    db: AsyncSession,
    title: str,
    created_by_user_id: int,
    member_user_ids: list[int],
) -> ChatThread:
    thread = ChatThread(
        thread_type="group",
        title=title,
        is_sales_team=False,
        created_by_user_id=_safe_user_id(created_by_user_id),
        created_at=func.now(),
        updated_at=func.now(),
    )
    db.add(thread)
    await db.flush()

    safe_ids = [uid for uid in set([created_by_user_id, *member_user_ids]) if uid and uid > 0]
    db.add_all([ChatThreadMember(thread_id=thread.id, user_id=uid) for uid in sorted(safe_ids)])
    await db.flush()
    return thread


async def add_members(db: AsyncSession, thread_id: int, user_ids: list[int]) -> int:
    if not user_ids:
        return 0

    existing_result = await db.execute(
        select(ChatThreadMember.user_id).where(ChatThreadMember.thread_id == thread_id)
    )
    existing = {int(uid) for (uid,) in existing_result.all()}
    to_add = [uid for uid in set(user_ids) if uid not in existing]
    db.add_all([ChatThreadMember(thread_id=thread_id, user_id=uid) for uid in to_add])
    await db.flush()
    return len(to_add)


async def remove_member(db: AsyncSession, thread_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(ChatThreadMember).where(
            ChatThreadMember.thread_id == thread_id, ChatThreadMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return False
    await db.delete(member)
    await db.flush()
    return True


async def list_messages(db: AsyncSession, thread_id: int, limit: int = 50, before_id: Optional[int] = None) -> list[ChatMessage]:
    stmt = select(ChatMessage).where(ChatMessage.thread_id == thread_id)
    if before_id is not None:
        stmt = stmt.where(ChatMessage.id < before_id)
    stmt = stmt.order_by(ChatMessage.id.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_message(
    db: AsyncSession,
    thread_id: int,
    sender_user_id: int,
    content: str,
    reply_to_message_id: Optional[int] = None,
) -> ChatMessage:
    msg = ChatMessage(
        thread_id=thread_id,
        sender_user_id=sender_user_id,
        content=content,
        reply_to_message_id=reply_to_message_id,
        created_at=func.now(),
    )
    db.add(msg)

    # bump thread updated_at
    thread_result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
    thread = thread_result.scalar_one_or_none()
    if thread:
        thread.updated_at = func.now()

    await db.flush()
    return msg


async def pin_message(db: AsyncSession, thread_id: int, message_id: int, pinned_by_user_id: int) -> bool:
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.thread_id == thread_id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        return False
    msg.is_pinned = True
    msg.pinned_by_user_id = _safe_user_id(pinned_by_user_id)
    msg.pinned_at = func.now()
    await db.flush()
    return True


async def unpin_message(db: AsyncSession, thread_id: int, message_id: int) -> bool:
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.thread_id == thread_id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        return False
    msg.is_pinned = False
    msg.pinned_by_user_id = None
    msg.pinned_at = None
    await db.flush()
    return True


async def mark_message_read(db: AsyncSession, message_id: int, user_id: int) -> bool:
    """Mark a specific message as read by a user."""
    # Check if message exists
    msg_result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    msg = msg_result.scalar_one_or_none()
    if not msg:
        return False

    # Check if already read
    existing = await db.execute(
        select(ChatMessageReadReceipt).where(
            ChatMessageReadReceipt.message_id == message_id,
            ChatMessageReadReceipt.user_id == user_id
        )
    )
    if existing.scalar_one_or_none():
        return True  # Already read

    # Create read receipt
    receipt = ChatMessageReadReceipt(
        message_id=message_id,
        user_id=user_id,
        read_at=func.now()
    )
    db.add(receipt)
    await db.flush()
    return True


async def mark_thread_read(db: AsyncSession, thread_id: int, user_id: int) -> int:
    """Mark all messages in a thread as read by a user. Returns count of messages marked."""
    # Get all message IDs in this thread that the user hasn't read yet
    # Exclude messages sent by the user themselves
    stmt = (
        select(ChatMessage.id)
        .where(
            ChatMessage.thread_id == thread_id,
            ChatMessage.sender_user_id != user_id
        )
    )
    msg_result = await db.execute(stmt)
    message_ids = [mid for (mid,) in msg_result.all()]

    if not message_ids:
        return 0

    # Get already read message IDs
    existing_result = await db.execute(
        select(ChatMessageReadReceipt.message_id).where(
            ChatMessageReadReceipt.message_id.in_(message_ids),
            ChatMessageReadReceipt.user_id == user_id
        )
    )
    already_read = {mid for (mid,) in existing_result.all()}

    # Mark the rest as read
    to_mark = [mid for mid in message_ids if mid not in already_read]
    for mid in to_mark:
        receipt = ChatMessageReadReceipt(
            message_id=mid,
            user_id=user_id,
            read_at=func.now()
        )
        db.add(receipt)

    await db.flush()
    return len(to_mark)


async def get_thread_unread_count(db: AsyncSession, thread_id: int, user_id: int) -> int:
    """Get count of unread messages in a thread for a user."""
    # Count messages in thread not sent by user and not yet read
    stmt = (
        select(func.count(ChatMessage.id))
        .outerjoin(
            ChatMessageReadReceipt,
            and_(
                ChatMessageReadReceipt.message_id == ChatMessage.id,
                ChatMessageReadReceipt.user_id == user_id
            )
        )
        .where(
            ChatMessage.thread_id == thread_id,
            ChatMessage.sender_user_id != user_id,
            ChatMessageReadReceipt.id.is_(None)
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_total_unread_count(db: AsyncSession, user_id: int) -> int:
    """Get total count of unread messages across all user's threads."""
    # Get all thread IDs user belongs to
    member_result = await db.execute(
        select(ChatThreadMember.thread_id).where(ChatThreadMember.user_id == user_id)
    )
    thread_ids = [tid for (tid,) in member_result.all()]

    if not thread_ids:
        return 0

    # Count unread messages across all these threads
    stmt = (
        select(func.count(ChatMessage.id))
        .outerjoin(
            ChatMessageReadReceipt,
            and_(
                ChatMessageReadReceipt.message_id == ChatMessage.id,
                ChatMessageReadReceipt.user_id == user_id
            )
        )
        .where(
            ChatMessage.thread_id.in_(thread_ids),
            ChatMessage.sender_user_id != user_id,
            ChatMessageReadReceipt.id.is_(None)
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0
