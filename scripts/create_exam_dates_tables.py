#!/usr/bin/env python3
import asyncio
import asyncpg
import os

async def main():
    db_url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🔧 Creating exam_dates table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_dates (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                description VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                max_registrations INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        print("🔧 Creating indexes for exam_dates...")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_exam_dates_date ON exam_dates (date)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_exam_dates_is_active ON exam_dates (is_active)")
        
        print("🔧 Creating exam_date_exams table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_date_exams (
                exam_date_id INTEGER NOT NULL REFERENCES exam_dates(id),
                exam_id INTEGER NOT NULL REFERENCES exams(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                PRIMARY KEY (exam_date_id, exam_id)
            )
        """)
        
        print("🔧 Creating exam_registrations table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_registrations (
                id SERIAL PRIMARY KEY,
                exam_date_id INTEGER NOT NULL REFERENCES exam_dates(id),
                exam_id INTEGER NOT NULL REFERENCES exams(id),
                examinee_id INTEGER NOT NULL REFERENCES examinees(id),
                status VARCHAR(20) DEFAULT 'registered',
                registration_code VARCHAR(20) NOT NULL UNIQUE,
                notes VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        print("🔧 Creating indexes for exam_registrations...")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_exam_registrations_exam_date_id ON exam_registrations (exam_date_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_exam_registrations_exam_id ON exam_registrations (exam_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_exam_registrations_examinee_id ON exam_registrations (examinee_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS ix_exam_registrations_status ON exam_registrations (status)")
        
        print("✅ All exam dates tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
