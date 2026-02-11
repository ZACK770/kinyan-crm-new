"""
Upload Shabat presentation files to R2 and create email template.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from db import SessionLocal, settings
from db.models import EmailTemplate, File
from services.storage import storage_service


async def main():
    """Upload Shabat files and create template."""
    
    # Define files to upload
    shabat_files = [
        "C:\\Users\\admin\\kinyan-crm-new\\presentation\\shabat\\שיעור דוגמא שבת.pdf",
        "C:\\Users\\admin\\kinyan-crm-new\\presentation\\shabat\\טעימה מתכנית כתר הוראה בשבת - קנין הוראה (1).pdf",
        "C:\\Users\\admin\\kinyan-crm-new\\presentation\\shabat\\מצגת קנין הוראה לדוגמא.pdf",
        "C:\\Users\\admin\\kinyan-crm-new\\presentation\\shabat\\סילבוס שבת קניין הוראה (1) (1).pdf",
    ]
    
    print("🔍 בדיקת הגדרות R2...")
    print(f"   Account ID: {storage_service.account_id}")
    print(f"   Bucket: {storage_service.bucket_name}")
    print(f"   Public URL: {storage_service.public_url or 'לא מוגדר'}")
    print(f"   Endpoint: https://{storage_service.account_id}.r2.cloudflarestorage.com")
    
    if not all([storage_service.account_id, storage_service.access_key, storage_service.secret_key]):
        print("❌ חסרים משתני סביבה נדרשים")
        return
    
    print("✅ הגדרות R2 תקינות")
    
    # Create database session
    async with SessionLocal() as db:
        # Step 1: Create email template
        print("\n📝 יוצר תבנית מייל למסלול שבת...")
        
        template = EmailTemplate(
            name="ליד מתעניין - מסלול שבת",
            subject="חומרי לימוד - מסלול הוראה בשבת",
            body_html="""
<div dir="rtl">
    <h2>שלום וברכה,</h2>
    
    <p>תודה על התעניינותך במסלול ההוראה בשבת של קניין הוראה!</p>
    
    <p>מצורפים אליך חומרי לימוד ומידע על המסלול:</p>
    <ul>
        <li>שיעור דוגמא מהמסלול</li>
        <li>טעימה מתכנית כתר הוראה בשבת</li>
        <li>מצגת הסבר על התכנית</li>
        <li>סילבוס מפורט של המסלול</li>
    </ul>
    
    <p>נשמח לענות על כל שאלה ולסייע בתהליך ההרשמה.</p>
    
    <p><strong>ניתן להירשם דרך הקישור:</strong> <a href="https://kinyanhoraah.co.il">kinyanhoraah.co.il</a></p>
    
    <p>בברכה,<br>
    צוות קניין הוראה</p>
</div>
            """.strip(),
            category="התרשמות",
            track_type="שבת",
            is_active=True,
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        print(f"✅ תבנית נוצרה - ID: {template.id}")
        
        # Step 2: Upload files to R2 and link to template
        print(f"\n📤 מעלה קבצים ל-R2 (Bucket: {storage_service.bucket_name})...")
        
        uploaded_count = 0
        for file_path in shabat_files:
            if not os.path.exists(file_path):
                print(f"⚠️  קובץ לא נמצא: {file_path}")
                continue
            
            filename = os.path.basename(file_path)
            print(f"   מעלה: {filename}...", end=" ")
            
            try:
                # Upload to R2
                with open(file_path, 'rb') as f:
                    result = await storage_service.upload_file(
                        file_data=f,
                        filename=filename,
                        folder=f"templates/{template.id}",
                        content_type="application/pdf"
                    )
                
                # Create file record in DB
                db_file = File(
                    filename=filename,
                    storage_key=result['key'],
                    content_type=result.get('content_type'),
                    size_bytes=result.get('size'),
                    entity_type="templates",
                    entity_id=template.id,
                    uploaded_by=None,
                    is_public=False,
                )
                db.add(db_file)
                
                file_size_mb = result.get('size', 0) / (1024 * 1024)
                print(f"✅ ({file_size_mb:.2f} MB)")
                uploaded_count += 1
                
            except Exception as e:
                print(f"❌ שגיאה: {e}")
        
        await db.commit()
        
        # Step 3: Verify template with attachments
        print(f"\n📋 בדיקת התבנית...")
        result = await db.execute(
            select(File).where(
                File.entity_type == "templates",
                File.entity_id == template.id
            )
        )
        attachments = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"✅ התבנית נוצרה בהצלחה!")
        print(f"{'='*60}")
        print(f"📌 שם התבנית: {template.name}")
        print(f"📌 ID: {template.id}")
        print(f"📌 נושא: {template.subject}")
        print(f"📌 קטגוריה: {template.category}")
        print(f"📌 מסלול: {template.track_type}")
        print(f"📌 קבצים מצורפים: {len(attachments)}")
        
        if attachments:
            print(f"\n📎 קבצים:")
            for att in attachments:
                size_mb = att.size_bytes / (1024 * 1024) if att.size_bytes else 0
                print(f"   • {att.filename} ({size_mb:.2f} MB)")
                print(f"     Storage key: {att.storage_key}")
        
        print(f"\n💡 כעת ניתן לשלוח מיילים עם התבנית דרך:")
        print(f"   POST /api/messages/send-email")
        print(f"   עם template_id={template.id}")


if __name__ == "__main__":
    asyncio.run(main())
