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
from db.models import User, ChatThread, ChatThreadMember, ChatMessage
from api.dependencies import get_current_user, require_permission
from services.auth import decode_access_token
from services.users import get_user_by_id
from services import chat as chat_svc

router = APIRouter()


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
def _msg_to_dict(msg: ChatMessage, sender: User | None = None, reply_preview: str | None = None) -> dict:
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

    return {
        "id": thread.id,
        "thread_type": thread.thread_type,
        "title": title,
        "is_sales_team": thread.is_sales_team,
        "members": members,
        "last_message": last_message,
        "created_at": str(thread.created_at) if thread.created_at else None,
        "updated_at": str(thread.updated_at) if thread.updated_at else None,
    }


# ── REST Endpoints ───────────────────────────────────

@router.get("/threads")
async def list_threads(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    threads = await chat_svc.list_threads_for_user(db, user)
    return [await _thread_to_dict(db, t, user.id) for t in threads]


@router.get("/threads/{thread_id}/messages")
async def get_messages(
    thread_id: int,
    before_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא או אין לך גישה")

    messages = await chat_svc.list_messages(db, thread_id, limit=limit, before_id=before_id)

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

    result_list = [
        _msg_to_dict(m, senders.get(m.sender_user_id), reply_previews.get(m.reply_to_message_id))
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
    thread = await chat_svc.get_thread_for_user(db, user, thread_id)
    if not thread:
        raise HTTPException(404, "שרשור לא נמצא או אין לך גישה")

    msg = await chat_svc.create_message(
        db, thread_id, user.id, body.content, body.reply_to_message_id
    )
    await db.commit()
    await db.refresh(msg)

    reply_preview = None
    if msg.reply_to_message_id:
        rr = await db.execute(select(ChatMessage).where(ChatMessage.id == msg.reply_to_message_id))
        rm = rr.scalar_one_or_none()
        if rm:
            reply_preview = rm.content[:60]

    msg_dict = _msg_to_dict(msg, user, reply_preview)

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
    if body.user_id == user.id:
        raise HTTPException(400, "לא ניתן לפתוח צ'אט עם עצמך")
    target = await get_user_by_id(db, body.user_id)
    if not target:
        raise HTTPException(404, "משתמש לא נמצא")

    thread = await chat_svc.get_or_create_dm_thread(db, user.id, body.user_id)
    await db.commit()
    return await _thread_to_dict(db, thread, user.id)


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

    # Also get count of recent messages (last 24h) in user's threads that aren't from the user
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.thread_id.in_(thread_ids),
            ChatMessage.sender_user_id != user.id,
            ChatMessage.created_at >= since,
        )
    )
    unread_count = count_result.scalar() or 0

    return {"notifications": notifications, "unread_count": unread_count}


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
