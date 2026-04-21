"""Test permission check directly"""
import asyncio
from db import get_db
from services.users import get_required_level, check_permission

async def test():
    async for db in get_db():
        try:
            # Test getting required level for tasks
            required = await get_required_level(db, "tasks", "edit")
            print(f"Required level for tasks/edit: {required}")
            
            # Test check permission
            user_level = 40  # admin
            has_perm = check_permission(user_level, required)
            print(f"Admin (40) has permission for tasks/edit (requires {required}): {has_perm}")
            
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

asyncio.run(test())
