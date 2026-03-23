# Alembic Migration Issues & Workarounds

## מה נתקלנו ואיך פתרנו

---

## 1. `alembic revision --autogenerate` נכשל עם `ConnectionRefusedError`

**תיאור הבעיה**
- כאשר ניסינו להריץ `alembic revision --autogenerate` אחרי שהוספנו מודל `GlobalTablePref`, הפקודה נכשלה עם:
  ```
  ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
  ```
- זה קרה כי Alembic מנסה להתחבר ל־DB כדי לסרוק את הסכמה ולהשוות התוצאה.

**פתרון**
- פנינו ליצירת **migration ידני** ללא חיבור:
  ```bash
  alembic revision -m "add global_table_prefs"
  ```
- ואז מילאנו ידנית את פקודות `create_table`/`create_index` בקובץ ה־migration.

**לקח לעתיד**
- עדיפות ליצור migration ידני כשהחיבור ל־DB לא יציב.
- זה גם מאפשר לכתוב SQL מותאם ולהפוך את ה־migration לאידמפוטנטי.

---

## 2. `alembic upgrade head` נכשל עם `DuplicateTableError`

**תיאור הבעיה**
- כשניסינו להריץ את ה־migration החדשה על ה־DB המרוחק, קיבלנו:
  ```
  sqlalchemy.exc.ProgrammingError: <class 'asyncpg.exceptions.DuplicateTableError'>: relation "global_table_prefs" already exists
  ```
- הסיבה: הטבלה כבר נוצרה בעבר על ידי מישהו אחר או ניסיונות קודמות, אבל Alembic לא סימן את הרביז’ן כרץ.

**פתרון**
- שינינו את ה־migration להיות **אידמפוטנטית**:
  ```python
  def upgrade() -> None:
      op.execute("""
          CREATE TABLE IF NOT EXISTS global_table_prefs ( ... );
      """)
      op.execute("""
          CREATE INDEX IF NOT EXISTS idx_global_table_prefs_storage_key
          ON global_table_prefs (storage_key);
      """)
  ```
- וכך ה־upgrade יצליח גם אם הטבלה כבר קיימת.

**לקח לעתיד**
- במקרים של טבלאות חדשות שאולי עלול להיווצר בסביבות מרובות (dev/test), תמיד להשתמש ב־`IF NOT EXISTS` ו־`IF NOT EXISTS` ב־migration למניעת התנגשויות.

---

## 3. `alembic upgrade head` נכשל עם `sslmode` לא נתמך

**תיאור הבעיה**
- כשהרצנו לראשון את ה־migration ל־`users.saved_filters`, קיבלנו שגיאת SSL ב־asyncpg:
  ```
  TypeError: connect() got an unexpected keyword argument 'sslmode'
  ```
- זה קרה כי `alembic.env.py` ניסה להעביר `sslmode` ל־`asyncpg` בצורה לא נכונה.

**פתרון**
- שינינו את `alembic/env.py` להעביר את `ssl=True` במקום `sslmode=require` ל־`asyncpg`:
  ```python
  connect_args={"ssl": True}
  ```

**לקח לעתיד**
- בעת שינויי `alembic/env.py`, תמיד לבדוק את הדרך הנכונה למנוע SSL עבור asyncpg.

---

## 4. חסימת חיבור ל־DB בזמן Migration

**תיאור הבעיה**
- בסביבות מקומיות או CI, לפעמים אין חיבור ל־DB המרוחק (רשת, VPN, חומתה).
- זה מונע גם אוטומטי וגם ידני של migrations.

**פתרון**
- השתמשו ב־`DATABASE_URL` עם `sslmode=require` במשתני סביבה כאשר מריצים migrations מקומית.
- אם זה לא עובד, השתמשו ב־`offline` mode של Alembic ליצירת SQL בלבד:
  ```bash
  alembic revision --autogenerate -m "desc" --sql
  ```

---

## 5. חוסרים סקריפטים ל־Python ב־`venv311`

**תיאור הבעיה**
- ניסינו להריץ `alembic` עם נתיב מסוים ל־`.venv311\Scripts\python.exe` אבל הנתיב לא היה קיים.

**פתרון**
- השתמשנו ב־`python` המערכתי של המערכת, או ב־`py -3.13` כדי להפעיל את ה־venv הנכון.

---

## סיכום הפתרונות שעבדו

| בעיה | פתרון |
|------|--------|
| `--autogenerate` נכשל עם ConnectionRefused | יצירת migration ידני (`alembic revision -m`) |
| DuplicateTableError ב־upgrade | עשהי את ה־SQL ל־`IF NOT EXISTS` |
| `sslmode` לא נתמך ב־asyncpg | השתמש ב־`connect_args={"ssl": True}` ב־`env.py` |
| חיבור ל־DB לא זמין | השתמש ב־`sslmode=require` ב־`DATABASE_URL` או offline mode |
| חסר נתיב ל־venv | השתמש ב־`python` המערכתי או `py -3.13` |

---

## טיפים לעתיד

1. **תמיד לפתח migrations בסביבת dev מקומית עם DB מקומי** לפני פריסה ל־DB מרוחק.
2. **לא לסמוך על `--autogenerate`** בסביבות לא יציבות.
3. **לעשות `alembic check` אחרי כל שינוי במודלים** כדי לוודא שהמיגרציה תואמת.
4. **לבדוק את ה־SQL שנוצר אוטומטית** לפני `upgrade head`.
5. **לגבות את הקבצים ב־`alembic/versions/` ב־git** אחרי כל מיגרציה פעילה.
