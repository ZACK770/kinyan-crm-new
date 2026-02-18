from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, Salesperson, ChatThread, ChatThreadMember, ChatMessage


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

    db.add_all(
        [
            ChatThreadMember(thread_id=thread.id, user_id=user_a_id),
            ChatThreadMember(thread_id=thread.id, user_id=user_b_id),
        ]
    )
    await db.flush()
    return thread


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
        created_by_user_id=created_by_user_id,
        created_at=func.now(),
        updated_at=func.now(),
    )
    db.add(thread)
    await db.flush()

    uniq = sorted(set([created_by_user_id, *member_user_ids]))
    db.add_all([ChatThreadMember(thread_id=thread.id, user_id=uid) for uid in uniq])
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
    msg.pinned_by_user_id = pinned_by_user_id
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
