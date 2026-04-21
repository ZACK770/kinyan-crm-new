"""Test task service directly without API"""
import asyncio
from datetime import datetime, timedelta
from db import get_db
from services import tasks as task_svc

async def test():
    async for db in get_db():
        try:
            # Try to create a task directly
            task = await task_svc.create_task(
                db,
                title="Direct Test Task",
                lead_id=6606,
                due_date=datetime.now() + timedelta(days=1),
                task_type="sales"
            )
            await db.commit()
            print(f"SUCCESS: Created task with ID {task.id}")
            print(f"Task: {task.title}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

asyncio.run(test())
