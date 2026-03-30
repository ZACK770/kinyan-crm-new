#!/usr/bin/env python3
"""
Seed script for exam dates demo data.
Creates sample exam dates and assigns existing exams to them.
"""
import asyncio
import asyncpg
import os
from datetime import date, datetime, timedelta

async def main():
    # Database connection
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return
    
    # Convert sqlalchemy URL to asyncpg format
    if db_url.startswith('postgresql+asyncpg://'):
        db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🌱 Seeding exam dates demo data...")
        
        # Create sample exam dates
        today = date.today()
        exam_dates = [
            {
                'date': today + timedelta(days=7),
                'description': 'מועד א',
                'is_active': True,
                'max_registrations': 30
            },
            {
                'date': today + timedelta(days=14),
                'description': 'מועד ב',
                'is_active': True,
                'max_registrations': 25
            },
            {
                'date': today + timedelta(days=21),
                'description': 'מועד ג',
                'is_active': True,
                'max_registrations': 20
            },
            {
                'date': today - timedelta(days=7),
                'description': 'מועד שעבר',
                'is_active': False,
                'max_registrations': None
            }
        ]
        
        # Insert exam dates
        exam_date_ids = []
        for ed in exam_dates:
            # Check if already exists
            existing = await conn.fetchval(
                "SELECT id FROM exam_dates WHERE date = $1",
                ed['date']
            )
            
            if existing:
                exam_date_ids.append(existing)
                print(f"✓ Exam date {ed['date']} already exists (ID: {existing})")
            else:
                exam_date_id = await conn.fetchval(
                    """
                    INSERT INTO exam_dates (date, description, is_active, max_registrations, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    ed['date'], ed['description'], ed['is_active'], ed['max_registrations'], datetime.now()
                )
                exam_date_ids.append(exam_date_id)
                print(f"✓ Created exam date {ed['date']} (ID: {exam_date_id})")
        
        # Get some existing exams
        exams = await conn.fetch(
            "SELECT id, name FROM exams ORDER BY id LIMIT 5"
        )
        
        if not exams:
            print("⚠️  No exams found. Please create some exams first.")
            return
        
        print(f"✓ Found {len(exams)} exams to assign")
        
        # Assign exams to dates (many-to-many)
        for i, exam_date_id in enumerate(exam_date_ids[:3]):  # Only active dates
            # Assign 2-3 exams to each date
            exams_for_date = exams[i:i+3] if i < len(exams) - 2 else exams[-3:]
            
            for exam in exams_for_date:
                # Check if already assigned
                existing = await conn.fetchval(
                    """
                    SELECT 1 FROM exam_date_exams 
                    WHERE exam_date_id = $1 AND exam_id = $2
                    """,
                    exam_date_id, exam['id']
                )
                
                if not existing:
                    await conn.execute(
                        """
                        INSERT INTO exam_date_exams (exam_date_id, exam_id, created_at)
                        VALUES ($1, $2, $3)
                        """,
                        exam_date_id, exam['id'], datetime.now()
                    )
                    print(f"✓ Assigned exam '{exam['name']}' to date {exam_date_id}")
                else:
                    print(f"✓ Exam '{exam['name']}' already assigned to date {exam_date_id}")
        
        # Create some sample registrations
        phone_numbers = ['0501234567', '0527180504', '0549876543']
        
        for i, exam_date_id in enumerate(exam_date_ids[:2]):  # Only first 2 active dates
            if i < len(exams) and i < len(phone_numbers):
                exam_id = exams[i]['id']
                phone = phone_numbers[i]
                
                # Check if examinee exists
                examinee_id = await conn.fetchval(
                    "SELECT id FROM examinees WHERE phone = $1",
                    phone
                )
                
                if not examinee_id:
                    # Create examinee - use only required fields
                    examinee_id = await conn.fetchval(
                        """
                        INSERT INTO examinees (phone, source, created_at)
                        VALUES ($1, $2, $3)
                        RETURNING id
                        """,
                        phone, 'demo', datetime.now()
                    )
                    print(f"✓ Created examinee {phone} (ID: {examinee_id})")
                
                # Check if already registered
                existing_reg = await conn.fetchval(
                    """
                    SELECT 1 FROM exam_registrations 
                    WHERE exam_date_id = $1 AND exam_id = $2 AND examinee_id = $3 AND status = 'registered'
                    """,
                    exam_date_id, exam_id, examinee_id
                )
                
                if not existing_reg:
                    # Generate registration code
                    import random
                    import string
                    registration_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    
                    await conn.execute(
                        """
                        INSERT INTO exam_registrations 
                        (exam_date_id, exam_id, examinee_id, status, registration_code, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        exam_date_id, exam_id, examinee_id, 'registered', registration_code, datetime.now()
                    )
                    print(f"✓ Created registration for {phone} (code: {registration_code})")
        
        print("\n🎉 Exam dates demo data seeded successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding exam dates: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
