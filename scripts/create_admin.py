"""
Script to create an admin user.
Usage: python -m scripts.create_admin
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import engine, SessionLocal, Base
from db.models import User
from services.auth import hash_password
from sqlalchemy import select


async def create_admin_user():
    """Create or update admin user."""
    email = "A0527698420@GMAIL.COM"
    password = "770880"
    full_name = "מנהל מערכת"
    
    async with SessionLocal() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Update existing user to admin
            existing_user.permission_level = 40
            existing_user.role_name = "admin"
            existing_user.hashed_password = hash_password(password)
            existing_user.is_active = True
            await db.commit()
            print(f"✅ משתמש קיים עודכן לאדמין: {email}")
            print(f"   רמת הרשאה: 40 (admin)")
        else:
            # Create new admin user
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                permission_level=40,
                role_name="admin",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            print(f"✅ משתמש אדמין חדש נוצר: {email}")
            print(f"   שם: {full_name}")
            print(f"   רמת הרשאה: 40 (admin)")
    
    print(f"\n📋 פרטי התחברות:")
    print(f"   אימייל: {email}")
    print(f"   סיסמה: {password}")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
