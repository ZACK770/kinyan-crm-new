"""
Replace shabat template files + add tahara & issur veheter files from extracted ZIP.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import select, delete
from db import SessionLocal
from db.models import EmailTemplate, File

BASE = Path(r"C:\Users\admin\Downloads\דוגמאות_temp\דוגמאות לשליחה")

TEMPLATE_FILES = [
    {
        "template_name": "ערכת התרשמות - קורס שבת",
        "folder": BASE / "שבת",
        "replace_old": True,  # delete old attachments first
    },
    {
        "template_name": "ערכת התרשמות - קורס טהרה",
        "folder": BASE / "טהרה",
        "replace_old": False,
    },
    {
        "template_name": "ערכת התרשמות - קורס איסור והיתר",
        "folder": BASE / "איסור והיתר",
        "replace_old": False,
    },
]


async def process_template(db, config):
    name = config["template_name"]
    folder = config["folder"]

    # Find template
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.name == name)
    )
    template = result.scalar_one_or_none()
    if not template:
        print(f"  ❌ Template '{name}' not found!")
        return

    template_id = template.id
    print(f"\n📋 {name} (id={template_id})")

    # Delete old attachments if needed
    if config["replace_old"]:
        result = await db.execute(
            select(File).where(
                File.entity_type == "templates",
                File.entity_id == template_id
            )
        )
        old_files = result.scalars().all()
        if old_files:
            print(f"  🗑 Deleting {len(old_files)} old attachments...")
            await db.execute(
                delete(File).where(
                    File.entity_type == "templates",
                    File.entity_id == template_id
                )
            )
            await db.commit()

    # Check existing attachments
    result = await db.execute(
        select(File).where(
            File.entity_type == "templates",
            File.entity_id == template_id
        )
    )
    existing_names = {f.filename for f in result.scalars().all()}

    # Upload new files one by one
    pdf_files = sorted(folder.glob("*.pdf"))
    print(f"  Found {len(pdf_files)} PDF files")

    for pdf_path in pdf_files:
        if pdf_path.name in existing_names:
            print(f"  ⏭ {pdf_path.name} — already attached")
            continue

        data = pdf_path.read_bytes()
        size = len(data)
        print(f"  Uploading {pdf_path.name} ({size / (1024*1024):.1f} MB)...")

        file_record = File(
            filename=pdf_path.name,
            storage_key=None,
            file_data=data,
            content_type="application/pdf",
            size_bytes=size,
            entity_type="templates",
            entity_id=template_id,
            uploaded_by=None,
            is_public=False,
        )
        db.add(file_record)
        await db.commit()
        print(f"  ✅ {pdf_path.name}")


async def main():
    async with SessionLocal() as db:
        for config in TEMPLATE_FILES:
            await process_template(db, config)

    print("\n✅ All templates updated!")


if __name__ == "__main__":
    asyncio.run(main())
