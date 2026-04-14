import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from db.models import File
from dotenv import load_dotenv

load_dotenv()

async def check_file():
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as db:
        result = await db.execute(select(File).where(File.id == 76))
        f = result.scalar_one_or_none()
        
        if f:
            print(f'File ID: {f.id}')
            print(f'Filename: {f.filename}')
            print(f'Storage Key: {f.storage_key}')
            print(f'Has file_data in DB: {bool(f.file_data)}')
            print(f'Size: {f.size_bytes} bytes')
            print(f'Entity: {f.entity_type} #{f.entity_id}')
            print(f'Created: {f.created_at}')
        else:
            print('File not found')

if __name__ == '__main__':
    asyncio.run(check_file())
