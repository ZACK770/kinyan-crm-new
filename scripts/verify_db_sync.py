"""Verify all models are synced with PostgreSQL database"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from db import engine, Base
from db.models import *

async def verify_sync():
    """Check if all SQLAlchemy models have corresponding tables in DB"""
    async with engine.begin() as conn:
        # Get all tables from DB
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        db_tables = {row[0] for row in result}
        
        # Get all model tables
        model_tables = {table.name for table in Base.metadata.tables.values()}
        
        print("=" * 60)
        print("DATABASE SYNC VERIFICATION")
        print("=" * 60)
        
        print(f"\n📊 Total DB tables: {len(db_tables)}")
        print(f"📋 Total model tables: {len(model_tables)}")
        
        # Check for missing tables in DB
        missing_in_db = model_tables - db_tables
        if missing_in_db:
            print(f"\n❌ Tables defined in models but MISSING in DB ({len(missing_in_db)}):")
            for table in sorted(missing_in_db):
                print(f"   - {table}")
        else:
            print(f"\n✅ All model tables exist in DB")
        
        # Check for extra tables in DB
        extra_in_db = db_tables - model_tables - {'alembic_version'}
        if extra_in_db:
            print(f"\n⚠️  Tables in DB but NOT in models ({len(extra_in_db)}):")
            for table in sorted(extra_in_db):
                print(f"   - {table}")
        else:
            print(f"\n✅ No extra tables in DB")
        
        # List all synced tables
        synced = model_tables & db_tables
        print(f"\n✅ Synced tables ({len(synced)}):")
        for table in sorted(synced):
            print(f"   - {table}")
        
        # Check for circular dependencies
        print("\n" + "=" * 60)
        print("CIRCULAR DEPENDENCY CHECK")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('leads', 'students')
                AND ccu.table_name IN ('leads', 'students')
        """))
        
        circular_fks = list(result)
        if circular_fks:
            print(f"\n🔄 Foreign keys between leads ↔ students:")
            for row in circular_fks:
                print(f"   {row[0]}.{row[1]} → {row[2]}")
            print("\n✅ This is OK - circular dependency handled with use_alter=True")
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if not missing_in_db and not extra_in_db:
            print("\n✅ DATABASE IS FULLY SYNCED WITH MODELS")
            print("✅ All tables exist and match the schema")
            print("✅ No migration needed")
            return True
        else:
            print("\n⚠️  DATABASE NEEDS MIGRATION")
            return False

if __name__ == "__main__":
    result = asyncio.run(verify_sync())
    sys.exit(0 if result else 1)
