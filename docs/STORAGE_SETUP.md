# הגדרת מערכת אחסון קבצים עם Cloudflare R2

## מה נוצר?

1. **Storage Service** ([services/storage.py](services/storage.py)) - שירות לניהול קבצים ב-R2
2. **File Model** ([db/models.py](db/models.py)) - טבלת `files` למעקב אחר קבצים
3. **Files API** ([api/files_api.py](api/files_api.py)) - Endpoints להעלאה והורדה של קבצים
4. **Migration** - מיגרציה ליצירת טבלת `files` במסד הנתונים

## התקנה מהירה

### שלב 1: התקן את boto3
```powershell
pip install boto3==1.34.0
```

### שלב 2: הרץ מיגרציה
```powershell
alembic upgrade head
```

### שלב 3: הגדר משתני סביבה

הוסף את המשתנים הבאים לקובץ `.env`:

```env
# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=crm-files
R2_PUBLIC_URL=https://files.yourdomain.com
```

## איך להוציא את פרטי ההתחברות מ-Cloudflare?

### יצירת Bucket ב-R2

1. היכנס ל-[Cloudflare Dashboard](https://dash.cloudflare.com/)
2. בחר **R2** מהתפריט הצדדי
3. לחץ על **Create bucket**
4. תן שם: `crm-files`
5. בחר מיקום (רצוי `EEUR` - Eastern Europe)

### יצירת API Token

1. בדף R2, לחץ על **Manage R2 API Tokens**
2. לחץ **Create API token**
3. שם: `crm-upload-token`
4. הרשאות: **Object Read & Write**
5. בחר את ה-Bucket: `crm-files`
6. לחץ **Create API Token**
7. **שמור** את:
   - **Access Key ID** → `R2_ACCESS_KEY_ID`
   - **Secret Access Key** → `R2_SECRET_ACCESS_KEY`
   - **Account ID** (בכתובת URL) → `R2_ACCOUNT_ID`

### הגדרת Domain ציבורי (אופציונלי)

אם אתה רוצה URL ציבורי לקבצים:

1. בדף הבאקט, לחץ על **Settings**
2. לחץ **Connect Domain**
3. הזן דומיין משלך (למשל: `files.yourdomain.com`)
4. הוסף CNAME record בהגדרות ה-DNS שלך
5. עדכן `R2_PUBLIC_URL=https://files.yourdomain.com` ב-.env

**בלי דומיין ציבורי:** הקבצים יהיו נגישים רק דרך Presigned URLs (לינקים זמניים).

## API Endpoints

### העלאת קובץ
```bash
POST /api/files/upload
Content-Type: multipart/form-data

# Parameters:
- file: File (required)
- entity_type: string (optional) - "leads", "students", "expenses"
- entity_id: integer (optional)
- description: string (optional)
- is_public: boolean (default: false)

# Example with curl:
curl -X POST "http://localhost:8000/api/files/upload?entity_type=leads&entity_id=123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

### רשימת קבצים
```bash
GET /api/files/
GET /api/files/?entity_type=leads&entity_id=123
```

### הורדת קובץ
```bash
GET /api/files/{file_id}/download
# מחזיר redirect ל-presigned URL
```

### מחיקת קובץ
```bash
DELETE /api/files/{file_id}
```

### קבצים של ישות מסוימת
```bash
GET /api/files/entity/{entity_type}/{entity_id}
# דוגמה: /api/files/entity/leads/123
```

## דוגמת שימוש ב-React

```typescript
// Upload file
async function uploadFile(file: File, entityType: string, entityId: number) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(
    `/api/files/upload?entity_type=${entityType}&entity_id=${entityId}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );
  
  return response.json();
}

// List files for a lead
async function getLeadFiles(leadId: number) {
  const response = await fetch(`/api/files/entity/leads/${leadId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}

// Download file
function downloadFile(fileId: number) {
  window.open(`/api/files/${fileId}/download`, '_blank');
}
```

## מגבלות ואבטחה

- **גודל קובץ מקסימלי:** 10MB (ניתן לשנות ב-`MAX_FILE_SIZE`)
- **אימות:** כל הנקודות דורשות Bearer token (חוץ מקבצים ציבוריים)
- **הרשאות:** משתמשים צריכים להיות מחוברים כדי להעלות/להוריד קבצים

## עלויות צפויות

**Cloudflare R2:**
- אחסון: $0.015/GB לחודש
- הורדות (egress): **$0 (בחינם!)**
- פעולות: $4.50 למיליון כתיבות, $0.36 למיליון קריאות

בשביל CRM קטן-בינוני: **~$1-5 לחודש**

## בעיות נפוצות

### שגיאה: "Missing R2 configuration"
- ודא שכל משתני הסביבה מוגדרים ב-.env
- הפעל מחדש את השרת אחרי שינוי .env

### שגיאה: "Upload failed"
- בדוק שה-API Token תקף
- ודא שה-Bucket קיים
- בדוק הרשאות של ה-Token

### הקבצים לא נגישים
- אם אין לך `R2_PUBLIC_URL`, השתמש ב-`/api/files/{id}/download`
- Presigned URLs תקפים ל-60 דקות בלבד

## תכונות עתידיות (אופציונלי)

- [ ] תמיכה בתמונות ממוזערות (thumbnails)
- [ ] סריקת וירוסים
- [ ] דחיסת תמונות
- [ ] גרסאות של קבצים
- [ ] הצפנה end-to-end
