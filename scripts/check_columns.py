"""
Check and add missing columns to leads table
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"

# Columns we need to add
REQUIRED_COLUMNS = {
    'lead_response': 'VARCHAR(100)',
    'follow_up_count': 'INTEGER DEFAULT 0',
    'last_contact_date': 'TIMESTAMP WITH TIME ZONE',
    'discount_notes': 'TEXT',
    'approval_method': 'VARCHAR(50)',
    'approval_date': 'TIMESTAMP WITH TIME ZONE',
}

async def check_and_add_columns():
    engine = create_async_engine(DATABASE_URL)
    
    try:
        async with engine.connect() as conn:
            # Get existing columns
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'leads'"
            ))
            existing_columns = {row[0] for row in result}
            
            print("Existing columns in 'leads' table:")
            for col in sorted(existing_columns):
                print(f"  ✓ {col}")
            
            print("\n" + "="*60)
            print("Checking required columns...")
            print("="*60 + "\n")
            
            # Check which columns are missing
            missing_columns = []
            for col_name, col_type in REQUIRED_COLUMNS.items():
                if col_name in existing_columns:
                    print(f"✓ {col_name} - EXISTS")
                else:
                    print(f"✗ {col_name} - MISSING")
                    missing_columns.append((col_name, col_type))
            
            # Add missing columns
            if missing_columns:
                print("\n" + "="*60)
                print(f"Adding {len(missing_columns)} missing columns...")
                print("="*60 + "\n")
                
                for col_name, col_type in missing_columns:
                    try:
                        alter_sql = f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}"
                        print(f"Executing: {alter_sql}")
                        await conn.execute(text(alter_sql))
                        await conn.commit()
                        print(f"  ✓ Added {col_name}")
                    except Exception as e:
                        print(f"  ✗ Error adding {col_name}: {e}")
                
                print("\n" + "="*60)
                print("✅ All missing columns added successfully!")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("✅ All required columns already exist!")
                print("="*60)
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_and_add_columns())
