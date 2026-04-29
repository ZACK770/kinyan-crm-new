"""
Chat API — internal team chat with DM, groups, replies, pins, WebSocket realtime.
Prefix: /api/chat
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from db import get_db
from db.models import User, ChatThread, ChatThreadMember, ChatMessage, ChatMessageReadReceipt
from api.dependencies import get_current_user, require_permission, DEV_SKIP_AUTH
from services.auth import decode_access_token
from services.users import get_user_by_id
from services import chat as chat_svc

router = APIRouter()

def _is_dev_user(user: User) -> bool:
    """Check if this is the fake dev user (id=0, DEV_SKIP_AUTH mode)."""
    return DEV_SKIP_AUTH and (not user.id or user.id == 0)


# ── Schemas ──────────────────────────────────────────
class ThreadResponse(BaseModel):
    id: int
    thread_type: str
    title: Optional[str] = None
    is_sales_team: bool
    members: list[dict] = []
    last_message: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    unread_count: int = 0


class MessageResponse(BaseModel):
    id: int
    thread_id: int
    sender_user_id: int
    sender_name: str
    sender_avatar: Optional[str] = None
    content: str
    reply_to_message_id: Optional[int] = None
    reply_to_preview: Optional[str] = None
    is_pinned: bool = False
    pinned_by_user_id: Optional[int] = None
    created_at: Optional[str] = None
    is_read: bool = False


class SendMessageRequest(BaseModel):
    content: str
    reply_to_message_id: Optional[int] = None


class CreateGroupRequest(BaseModel):
    title: str
    member_user_ids: list[int]


class AddMembersRequest(BaseModel):
    user_ids: list[int]


class StartDMRequest(BaseModel):
    user_id: int


# ── WebSocket connection manager ─────────────────────
class ChatConnectionManager:
    def __init__(self):
        # thread_id -> set of (user_id, websocket)
        self._connections: dict[int, set[tuple[int, WebSocket]]] = {}
        # user_id -> set of websockets (for global notifications)
        self._user_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, user_id: int, thread_id: int):
        await ws.accept()
        if thread_id not in self._connections:
            self._connections[thread_id] = set()
        self._connections[thread_id].add((user_id, ws))
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(ws)

    def disconnect(self, ws: WebSocket, user_id: int, thread_id: int):
        if thread_id in self._connections:
            self._connections[thread_id].discard((user_id, ws))
            if not self._connections[thread_id]:
                del self._connections[thread_id]
        if user_id in self._user_connections:
            self._user_connections[user_id].discard(ws)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

    async def broadcast_to_thread(self, thread_id: int, message: dict, exclude_user_id: int | None = None):
        if thread_id not in self._connections:
            return
        dead = []
        for uid, ws in self._connections[thread_id]:
            if exclude_user_id and uid == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append((uid, ws))
        for item in dead:
            self._connections[thread_id].discard(item)

    async def notify_user(self, user_id: int, message: dict):
        if user_id not in self._user_connections:
            return
        dead = []
        for ws in self._user_connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._user_connections[user_id].discard(ws)


manager = ChatConnectionManager()


# ── Helpers ──────────────────────────────────────────
def _msg_to_dict(msg: ChatMessage, sender: User | None = None, reply_preview: str | None = None, is_read: bool = False, read_by_count: int = 0, total_members: int = 0) -> dict:
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "sender_user_id": msg.sender_user_id,
        "sender_name": sender.full_name if sender else "?",
        "sender_avatar": sender.avatar_url if sender else None,
        "content": msg.content,
        "reply_to_message_id": msg.reply_to_message_id,
        "reply_to_preview": reply_preview,
        "is_pinned": msg.is_pinned,
        "pinned_by_user_id": msg.pinned_by_user_id,
        "created_at": str(msg.created_at) if msg.created_at else None,
        "is_read": is_read,
        "read_by_count": read_by_count,
        "total_members": total_members,
    }


async def _thread_to_dict(db: AsyncSession, thread: ChatThread, current_user_id: int) -> dict:
    # Members
    members_result = await db.execute(
        select(ChatThreadMember, User)
        .join(User, User.id == ChatThreadMember.user_id)
        .where(ChatThreadMember.thread_id == thread.id)
    )
    members = [
        {"user_id": m.user_id, "full_name": u.full_name, "avatar_url": u.avatar_url}
        for m, u in members_result.all()
    ]

    # DM title: show the other person's name
    title = thread.title
    if thread.thread_type == "dm" and not title:
        other = [m for m in members if m["user_id"] != current_user_id]
        title = other[0]["full_name"] if other else "צ'אט פרטי"

    # Last message
    last_msg_result = await db.execute(
        select(ChatMessage, User)
        .join(User, User.id == ChatMessage.sender_user_id)
        .where(ChatMessage.thread_id == thread.id)
        .order_by(ChatMessage.id.desc())
        .limit(1)
    )
    last_row = last_msg_result.first()
    last_message = None
    if last_row:
        lm, lu = last_row
        last_message = {
            "id": lm.id,
            "sender_name": lu.full_name,
            "content": lm.content[:80],
            "created_at": str(lm.created_at) if lm.created_at else None,
        }

    # Unread count
    unread_count = await chat_svc.get_thread_unread_count(db, thread.id, current_user_id)

    return {
        "id": thread.id,
        "thread_type": thread.thread_type,
        "title": title,
        "is_sales_team": thread.is_sales_team,
        "members": members,
        "last_message": last_message,
        "created_at": str(thread.created_at) if thread.created_at else None,
        "updated_at": str(thread.updated_at) if thread.updated_at else None,
        "unread_count": unread_count,
    }


# ── REST Endpoints ───────────────────────────────────

@router.get("/threads")
async def list_threads(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if _is_dev_user(user):
        # Dev user: show all threads
        result = await db.execute(
            select(ChatThread).order_by(ChatThread.updated_at.desc().nullslast(), ChatThread.created_at.desc())
        )
        threads = list(result.scalars().unique().all())
    else:
        threads = await chat_svc.list_threads_for_user(db, user)
    return [await _thread_to_dict(db, t, user.id or 0) for t in threads]


@router.get("/threads/{thread_id}/messages")
async def get_messages(
    thread_id: int,
    before_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if _is_dev_user(user):
        result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
        thread = result.scalar_one_or_none()
    else:
        thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא או אין לך גישה")

    messages = await chat_svc.list_messages(db, thread_id, limit=limit, before_id=before_id)

    # Get total thread members count
    members_result = await db.execute(
        select(func.count(ChatThreadMember.id)).where(ChatThreadMember.thread_id == thread_id)
    )
    total_members = members_result.scalar() or 0

    # Collect senders
    sender_ids = list({m.sender_user_id for m in messages})
    senders: dict[int, User] = {}
    if sender_ids:
        result = await db.execute(select(User).where(User.id.in_(sender_ids)))
        senders = {u.id: u for u in result.scalars().all()}

    # Collect reply previews
    reply_ids = [m.reply_to_message_id for m in messages if m.reply_to_message_id]
    reply_previews: dict[int, str] = {}
    if reply_ids:
        result = await db.execute(select(ChatMessage).where(ChatMessage.id.in_(reply_ids)))
        for rm in result.scalars().all():
            reply_previews[rm.id] = rm.content[:60]

    # Collect read receipts for current user
    message_ids = [m.id for m in messages]
    read_receipts: set[int] = set()
    if message_ids and user.id:
        result = await db.execute(
            select(ChatMessageReadReceipt.message_id).where(
                ChatMessageReadReceipt.message_id.in_(message_ids),
                ChatMessageReadReceipt.user_id == user.id
            )
        )
        read_receipts = {mid for (mid,) in result.all()}

    # Collect read counts for each message
    read_counts: dict[int, int] = {}
    if message_ids:
        result = await db.execute(
            select(ChatMessageReadReceipt.message_id, func.count(ChatMessageReadReceipt.id))
            .where(ChatMessageReadReceipt.message_id.in_(message_ids))
            .group_by(ChatMessageReadReceipt.message_id)
        )
        read_counts = {mid: count for mid, count in result.all()}

    result_list = [
        _msg_to_dict(
            m,
            senders.get(m.sender_user_id),
            reply_previews.get(m.reply_to_message_id),
            m.id in read_receipts,
            read_counts.get(m.id, 0),
            total_members
        )
        for m in messages
    ]
    result_list.reverse()  # oldest first
    return result_list


@router.post("/threads/{thread_id}/messages")
async def send_message(
    thread_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if _is_dev_user(user):
        result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
        thread = result.scalar_one_or_none()
        # Use first real admin user as sender to avoid FK violation
        real_user_result = await db.execute(
            select(User).where(User.is_active == True, User.permission_level >= 30).limit(1)  # noqa: E712
        )
        real_user = real_user_result.scalar_one_or_none()
        sender_id = real_user.id if real_user else 1
        sender_for_dict = real_user or user
    else:
        thread = await chat_svc.get_thread_for_user(db, user, thread_id)
        sender_id = user.id
        sender_for_dict = user
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא או אין לך גישה")

    msg = await chat_svc.create_message(
        db, thread_id, sender_id, body.content, body.reply_to_message_id
    )
    await db.commit()
    await db.refresh(msg)

    reply_preview = None
    if msg.reply_to_message_id:
        rr = await db.execute(select(ChatMessage).where(ChatMessage.id == msg.reply_to_message_id))
        rm = rr.scalar_one_or_none()
        if rm:
            reply_preview = rm.content[:60]

    # Get total members count
    members_result = await db.execute(
        select(func.count(ChatThreadMember.id)).where(ChatThreadMember.thread_id == thread_id)
    )
    total_members = members_result.scalar() or 0

    msg_dict = _msg_to_dict(msg, sender_for_dict, reply_preview, False, 0, total_members)

    # Broadcast via WebSocket
    await manager.broadcast_to_thread(thread_id, {
        "type": "new_message",
        "thread_id": thread_id,
        "message": msg_dict,
    })

    return msg_dict


@router.post("/threads/dm")
async def start_dm(
    body: StartDMRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # In dev mode, use a real user to avoid broken DM threads (id=0 gets filtered)
    if _is_dev_user(user):
        real_user_result = await db.execute(
            select(User).where(User.is_active == True, User.permission_level >= 30).limit(1)  # noqa: E712
        )
        real_user = real_user_result.scalar_one_or_none()
        effective_user_id = real_user.id if real_user else 1
    else:
        effective_user_id = user.id

    if body.user_id == effective_user_id:
        raise HTTPException(400, "לא ניתן לפתוח צ'אט עם עצמך")
    target = await get_user_by_id(db, body.user_id)
    if not target:
        raise HTTPException(404, "משתמש לא נמצא")

    thread = await chat_svc.get_or_create_dm_thread(db, effective_user_id, body.user_id)
    await db.commit()
    return await _thread_to_dict(db, thread, effective_user_id)


@router.post("/threads/group")
async def create_group(
    body: CreateGroupRequest,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    if not body.title.strip():
        raise HTTPException(400, "נא להזין שם לקבוצה")
    thread = await chat_svc.create_group_thread(db, body.title.strip(), user.id, body.member_user_ids)
    await db.commit()
    return await _thread_to_dict(db, thread, user.id)


@router.get("/threads/sales-team")
async def get_sales_team_thread(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = await chat_svc.get_or_create_sales_team_thread(db)
    # Ensure current user is a member (auto-add managers/admins)
    if user.id and user.id > 0 and user.permission_level >= 30:
        await chat_svc.add_members(db, thread.id, [user.id])
    await db.commit()
    return await _thread_to_dict(db, thread, user.id)


@router.post("/threads/{thread_id}/members")
async def add_thread_members(
    thread_id: int,
    body: AddMembersRequest,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא")
    if thread.thread_type == "dm":
        raise HTTPException(400, "לא ניתן להוסיף חברים לצ'אט פרטי")
    added = await chat_svc.add_members(db, thread_id, body.user_ids)
    await db.commit()
    return {"added": added}


@router.delete("/threads/{thread_id}/members/{member_user_id}")
async def remove_thread_member(
    thread_id: int,
    member_user_id: int,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא")
    removed = await chat_svc.remove_member(db, thread_id, member_user_id)
    await db.commit()
    if not removed:
        raise HTTPException(404, "החבר לא נמצא בשרשור")
    return {"removed": True}


@router.post("/threads/{thread_id}/messages/{message_id}/pin")
async def pin_msg(
    thread_id: int,
    message_id: int,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    ok = await chat_svc.pin_message(db, thread_id, message_id, user.id)
    await db.commit()
    if not ok:
        raise HTTPException(404, "הודעה לא נמצאה")

    await manager.broadcast_to_thread(thread_id, {
        "type": "message_pinned",
        "thread_id": thread_id,
        "message_id": message_id,
        "pinned_by": user.full_name,
    })
    return {"pinned": True}


@router.delete("/threads/{thread_id}/messages/{message_id}/pin")
async def unpin_msg(
    thread_id: int,
    message_id: int,
    user: User = Depends(require_permission("manager")),
    db: AsyncSession = Depends(get_db),
):
    ok = await chat_svc.unpin_message(db, thread_id, message_id)
    await db.commit()
    if not ok:
        raise HTTPException(404, "הודעה לא נמצאה")

    await manager.broadcast_to_thread(thread_id, {
        "type": "message_unpinned",
        "thread_id": thread_id,
        "message_id": message_id,
    })
    return {"unpinned": True}


@router.get("/threads/{thread_id}/pinned")
async def get_pinned_messages(
    thread_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא")

    result = await db.execute(
        select(ChatMessage, User)
        .join(User, User.id == ChatMessage.sender_user_id)
        .where(ChatMessage.thread_id == thread_id, ChatMessage.is_pinned == True)  # noqa: E712
        .order_by(ChatMessage.pinned_at.desc())
    )
    return [
        _msg_to_dict(m, u)
        for m, u in result.all()
    ]


@router.get("/users/available")
async def get_available_users(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active users for starting DM / adding to groups."""
    result = await db.execute(
        select(User)
        .where(User.is_active == True, User.permission_level >= 10)  # noqa: E712
        .order_by(User.full_name)
    )
    return [
        {"id": u.id, "full_name": u.full_name, "avatar_url": u.avatar_url, "role_name": u.role_name}
        for u in result.scalars().all()
        if u.id != user.id
    ]


# ── Notifications (for Header bell) ──────────────────

@router.get("/notifications")
async def get_chat_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get chat notifications for the current user:
    - Messages that mention the user by name (e.g. @שם)
    - Recent messages in threads the user belongs to
    Returns last 20 notifications sorted by newest first.
    """
    # Get all thread IDs user belongs to
    member_result = await db.execute(
        select(ChatThreadMember.thread_id).where(ChatThreadMember.user_id == user.id)
    )
    thread_ids = [tid for (tid,) in member_result.all()]

    if not thread_ids:
        return {"notifications": [], "unread_count": 0}

    # Find messages that mention this user (by name) — last 20
    # Also include pinned messages as notifications
    mention_pattern = f"@{user.full_name}"

    stmt = (
        select(ChatMessage, User)
        .join(User, User.id == ChatMessage.sender_user_id)
        .where(
            ChatMessage.thread_id.in_(thread_ids),
            ChatMessage.sender_user_id != user.id,
            or_(
                ChatMessage.content.contains(mention_pattern),
                ChatMessage.is_pinned == True,  # noqa: E712
            )
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    rows = result.all()

    notifications = []
    for msg, sender in rows:
        is_mention = mention_pattern in msg.content
        notifications.append({
            "id": msg.id,
            "type": "mention" if is_mention else "pin",
            "thread_id": msg.thread_id,
            "sender_name": sender.full_name,
            "sender_avatar": sender.avatar_url,
            "content": msg.content[:100],
            "created_at": str(msg.created_at) if msg.created_at else None,
        })

    # Get total unread count using the new function
    unread_count = await chat_svc.get_total_unread_count(db, user.id or 0)

    return {"notifications": notifications, "unread_count": unread_count}


# ── Read Receipts Endpoints ───────────────────────────

@router.post("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific message as read by the current user."""
    success = await chat_svc.mark_message_read(db, message_id, user.id or 0)
    await db.commit()
    if not success:
        raise HTTPException(404, "הודעה לא נמצאה")

    # Get thread_id for broadcasting
    msg_result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    message = msg_result.scalar_one_or_none()
    if message:
        # Broadcast read receipt update to thread
        await manager.broadcast_to_thread(message.thread_id, {
            "type": "message_read",
            "message_id": message_id,
            "user_id": user.id,
            "user_name": user.full_name,
        })

    return {"read": True}


@router.post("/threads/{thread_id}/mark-read")
async def mark_thread_as_read(
    thread_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all messages in a thread as read by the current user."""
    if _is_dev_user(user):
        result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
        thread = result.scalar_one_or_none()
    else:
        thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא או אין לך גישה")

    count = await chat_svc.mark_thread_read(db, thread_id, user.id or 0)
    await db.commit()
    return {"marked_count": count}


@router.get("/threads/{thread_id}/members")
async def get_thread_members(
    thread_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of thread members for @mention autocomplete."""
    if _is_dev_user(user):
        result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
        thread = result.scalar_one_or_none()
    else:
        thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא או אין לך גישה")

    result = await db.execute(
        select(ChatThreadMember, User)
        .join(User, ChatThreadMember.user_id == User.id)
        .where(ChatThreadMember.thread_id == thread_id)
    )
    members = []
    for member, u in result.all():
        members.append({
            "id": u.id,
            "name": u.full_name,
            "avatar": u.avatar_url,
        })
    return members


@router.get("/messages/{message_id}/read-receipts")
async def get_message_read_receipts(
    message_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of users who read a specific message."""
    # Verify message exists and user has access
    msg_result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    message = msg_result.scalar_one_or_none()
    if not message:
        raise HTTPException(404, "הודעה לא נמצאה")

    # Verify user is member of the thread
    if _is_dev_user(user):
        thread_result = await db.execute(select(ChatThread).where(ChatThread.id == message.thread_id))
        thread = thread_result.scalar_one_or_none()
    else:
        thread = await chat_svc.get_thread_for_user(db, user, message.thread_id)

    if not thread:
        raise HTTPException(403, "אין לך גישה להודעה זו")

    # Get all thread members
    members_result = await db.execute(
        select(ChatThreadMember, User)
        .join(User, User.id == ChatThreadMember.user_id)
        .where(ChatThreadMember.thread_id == message.thread_id)
    )
    members = [(m, u) for m, u in members_result.all()]

    # Get read receipts for this message
    receipts_result = await db.execute(
        select(ChatMessageReadReceipt).where(ChatMessageReadReceipt.message_id == message_id)
    )
    receipts = {r.user_id: r.read_at for r in receipts_result.scalars().all()}

    # Build response with read status for each member
    receipts_list = []
    for member, user_obj in members:
        read_at = receipts.get(member.user_id)
        receipts_list.append({
            "user_id": member.user_id,
            "full_name": user_obj.full_name,
            "avatar_url": user_obj.avatar_url,
            "read_at": str(read_at) if read_at else None,
            "is_read": read_at is not None
        })

    return {"receipts": receipts_list}


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a message (only by sender or admin)."""
    result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(404, "הודעה לא נמצאה")

    # Only sender can delete their own message (or admin)
    if message.sender_user_id != user.id and not user.is_superuser:
        raise HTTPException(403, "אין לך הרשאה למחוק הודעה זו")

    await db.delete(message)
    await db.commit()
    return {"deleted": True}


# ── WebSocket endpoint ───────────────────────────────

@router.websocket("/ws/{thread_id}")
async def chat_websocket(ws: WebSocket, thread_id: int):
    """
    WebSocket for real-time chat.
    Client sends token as first message for auth.
    Then listens for broadcasts.
    """
    # Wait for auth message
    await ws.accept()
    try:
        auth_msg = await asyncio.wait_for(ws.receive_text(), timeout=10)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        await ws.close(code=4001)
        return

    # Validate token
    payload = decode_access_token(auth_msg)
    if not payload:
        await ws.send_json({"type": "error", "detail": "טוקן לא תקין"})
        await ws.close(code=4001)
        return

    user_id = int(payload.get("sub", 0))

    # Re-register with manager (we already accepted above, so just track)
    if thread_id not in manager._connections:
        manager._connections[thread_id] = set()
    manager._connections[thread_id].add((user_id, ws))
    if user_id not in manager._user_connections:
        manager._user_connections[user_id] = set()
    manager._user_connections[user_id].add(ws)

    await ws.send_json({"type": "connected", "thread_id": thread_id, "user_id": user_id})

    try:
        while True:
            # Keep connection alive; client can send pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws, user_id, thread_id)
