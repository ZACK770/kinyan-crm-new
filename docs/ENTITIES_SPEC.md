# Kinyan CRM — אפיון ישויות מלא

> מסמך ייחוס לכל הטבלאות במערכת. 21 ישויות (17 מאופיינות + 4 לאפיון עתידי).
> עדכון אחרון: 2026-02-10

---

## סטטוס בנייה

| # | ישות | טבלה | מודל Python | סטטוס |
|---|------|-------|-------------|-------|
| 1 | לידים | `leads` | `Lead` | ✅ קיים — להשלמת שדות |
| 2 | תלמידים | `students` | `Student` | ✅ קיים — להשלמת שדות |
| 3 | קמפיינים | `campaigns` | `Campaign` | ✅ קיים — להשלמת שדות |
| 4 | אנשי מכירות | `salespeople` | `Salesperson` | ✅ קיים — להשלמת שדות |
| 5 | משימות מכירות | `sales_tasks` | `SalesTask` | ✅ קיים — להשלמת שדות |
| 6 | הודעות לידים | `lead_messages` | `LeadMessage` | 🔨 חסר |
| 7 | פניות נכנסות | `inquiries` | `Inquiry` | 🔨 חסר |
| 8 | קורסים | `courses` | `Course` | ✅ קיים — להשלמת שדות |
| 9 | שיעורים/מודולים | `course_modules` | `CourseModule` | ✅ קיים — להשלמת שדות |
| 10 | מרצים | `lecturers` | `Lecturer` | 🔨 חסר |
| 11 | מבחנים | `exams` | `Exam` | ✅ קיים — לשדרוג מבני |
| 12 | נוכחות ומטלות | `attendance` | `Attendance` | 🔨 חסר |
| 13 | תשלומים | `payments` | `Payment` | ✅ קיים — להשלמת שדות |
| 14 | התחייבויות | `commitments` | `Commitment` | 🔨 חסר |
| 15 | קופונים | `coupons` | `Coupon` | ✅ קיים — להשלמת שדות |
| 16 | גביה | `collections` | `Collection` | 🔨 חסר |
| 17 | הוצאות | `expenses` | `Expense` | 🔨 חסר |
| — | מוצרים | `products` | `Product` | ✅ קיים (עזר) |
| — | אינטראקציות ליד | `lead_interactions` | `LeadInteraction` | ✅ קיים |
| — | מוצרי ליד | `lead_products` | `LeadProduct` | ✅ קיים |
| — | הרשמות | `enrollments` | `Enrollment` | ✅ קיים |

### טבלאות ילד (repeatable)
| טבלה | ישות-אב | סטטוס |
|-------|---------|-------|
| `campaign_salesperson_links` | קמפיינים | 🔨 חסר |
| `campaign_landing_links` | קמפיינים | 🔨 חסר |
| `exam_submissions` | מבחנים | 🔨 חסר |
| `task_reports` | משימות מכירות | 🔨 חסר |
| `inquiry_responses` | פניות נכנסות | 🔨 חסר |

---

## 1. לידים (`leads`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| מספר ליד | `id` | auto-increment PK | אוטומטי | |
| שם מלא | `full_name` | String(300) | כן | |
| שם משפחה | `family_name` | String(200) | לא | |
| טלפון ראשי | `phone` | String(50) | כן | ייחודי, מנורמל |
| טלפון נוסף | `phone2` | String(50) | לא | |
| מייל | `email` | String(200) | לא | |
| כתובת | `address` | Text | לא | |
| עיר מגורים | `city` | String(200) | לא | |
| תעודת זהות | `id_number` | String(20) | לא | |
| הערות | `notes` | Text | לא | |
| **מקור הגעה** | | | | |
| מקור כללי | `source_type` | String(100) | לא | אלמנטור / ימות / ידני / אחר |
| שם המפרסם | `source_name` | String(300) | לא | |
| שם קמפיין (טקסט) | `campaign_name` | String(300) | לא | |
| קמפיין (FK) | `campaign_id` | FK → campaigns | לא | קישור ישיר |
| תאריך הגעה | `arrival_date` | DateTime | אוטומטי | |
| הודעה מהליד | `source_message` | Text | לא | |
| פרטים נוספים | `source_details` | Text | לא | |
| **שיוך מכירות** | | | | |
| איש מכירות | `salesperson_id` | FK → salespeople | לא | round-robin |
| סטטוס ליד | `status` | String(100) | כן | ליד חדש / חיוג ראשון / במעקב / מתעניין / נסלק / ליד סגור-לקוח / ליד סגור-לא רלוונטי |
| **שלבי המרה** | | | | |
| נסלק חיוב ראשון | `first_payment` | Boolean | לא | |
| השתתף בשיעור ראשון | `first_lesson` | Boolean | לא | |
| אישר תקנון | `approved_terms` | Boolean | לא | |
| תאריך המרה | `conversion_date` | DateTime | לא | |
| קישור לתלמיד | `student_id` | FK → students | לא | |
| משימה פעילה | `active_task_id` | FK → sales_tasks | לא | |
| **מכירה וסליקה** | | | | |
| מוצר שנבחר | `selected_product_id` | FK → lead_products | לא | המוצר שנבחר לעסקה |
| תשלום ראשון | `first_payment_id` | FK → payments | לא | התשלום הראשון שנסלק |
| לינק תשלום נדרים | `nedarim_payment_link` | String(500) | לא | לינק פעיל לתשלום |
| **מטא** | | | | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |
| תאריך עדכון | `updated_at` | DateTime | אוטומטי | |
| נוצר על ידי | `created_by` | String(200) | אוטומטי | |

**מופעים מקושרים (יוצגו בדף ליד):**
- תקשורת (`lead_interactions`) — תאריך, משתמש, תיאור, תאריך שיחה הבאה
- פניות IVR (`lead_interactions` type=ivr_call) — תאריך, סטטוס מענה, זמן המתנה, אורך שיחה, שלוחת מוצר
- פניות אתר (`lead_interactions` type=website_form) — תאריך, מוצר מתעניין, תוכן
- פניות נכנסות (`inquiries`) — מישות פניות
- משימות מכירות (`sales_tasks`) — כל המשימות על הליד
- תשלומים (`payments`) — אם שילם
- מוצרים (`lead_products`) — מוצרים שמתעניין בהם

---

## 2. תלמידים (`students`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| מספר תלמיד | `id` | auto-increment PK | אוטומטי | |
| שם התלמיד | `full_name` | String(300) | כן | |
| סטטוס | `status` | String(100) | כן | פעיל / מושהה / סיים / עזב |
| מספר זהות | `id_number` | String(20) | לא | |
| טלפון נייד | `phone` | String(50) | כן | |
| טלפון נוסף | `phone2` | String(50) | לא | |
| כתובת | `address` | Text | לא | |
| עיר | `city` | String(200) | לא | |
| כתובת מייל | `email` | String(200) | לא | |
| הערות | `notes` | Text | לא | |
| אישר תקנון | `approved_terms` | Boolean | לא | |
| קישור לליד | `lead_id` | FK → leads | לא | |
| מזהה נדרים | `nedarim_id` | String(50) | לא | |
| **פרטי תשלום** | | | | |
| מחיר לתשלום | `total_price` | Numeric(10,2) | לא | סה"כ עסקה |
| שולם | `total_paid` | Numeric(10,2) | לא | מעודכן אוטו מתשלומים |
| יתרה לתשלום | — | formula | אוטומטי | total_price - total_paid |
| סטטוס תשלום | `payment_status` | String(50) | לא | שולם / חוב / בתשלומים |
| סטטוס משלוח | `shipping_status` | String(50) | לא | ממתין / נשלח / התקבל |
| **מטא** | | | | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |
| תאריך עדכון | `updated_at` | DateTime | אוטומטי | |

**מופעים מקושרים:**
- הרשמות לקורסים (`enrollments`) — קורס, תאריך, מחיר
- מבחנים + ציונים (`exam_submissions`)
- נוכחות ומטלות (`attendance`)
- תשלומים (`payments`)
- התחייבויות (`commitments`)
- פניות נכנסות (`inquiries`) — אם קושרו אליו

---

## 3. קמפיינים (`campaigns`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| מספר קמפיין | `id` | auto-increment PK | אוטומטי | |
| שם הקמפיין | `name` | String(300) | כן | |
| קורס | `course_id` | FK → courses | לא | |
| במות פרסום | `platforms` | Text | לא | פייסבוק, גוגל, ימות... (comma-separated) |
| תאריך התחלה | `start_date` | Date | לא | |
| תאריך סיום | `end_date` | Date | לא | |
| שם טופס הרשמה | `form_name` | String(300) | לא | |
| קישור לדף נחיתה | `landing_page_url` | String(500) | לא | |
| תיאור/הערות | `description` | Text | לא | |
| פעיל | `is_active` | Boolean | כן | default: true |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

**טבלת ילד — לינקים לאנשי מכירות (`campaign_salesperson_links`):**

| שדה | עמודה | סוג | הערה |
|-----|-------|-----|------|
| id | `id` | PK | |
| קמפיין | `campaign_id` | FK → campaigns | |
| איש מכירות | `salesperson_id` | FK → salespeople | |
| טקסט הודעה | `message_text` | Text | |

**טבלת ילד — לינקים לדף נחיתה (`campaign_landing_links`):**

| שדה | עמודה | סוג | הערה |
|-----|-------|-----|------|
| id | `id` | PK | |
| קמפיין | `campaign_id` | FK → campaigns | |
| מקור הרשמה | `source_label` | String(200) | UTM source |
| קישור עם מקור | `url_with_source` | String(500) | |

**מופעים מקושרים:** לידים שהגיעו מהקמפיין

---

## 4. אנשי מכירות (`salespeople`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| שם | `name` | String(200) | כן | |
| מייל | `email` | String(200) | לא | |
| טלפון נייד | `phone` | String(50) | לא | |
| קוד ייחוס | `ref_code` | String(50) | לא | |
| הערות | `notes` | Text | לא | |
| פעיל | `is_active` | Boolean | כן | default: true |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

**מופעים מקושרים:** לידים משויכים, משימות פתוחות

---

## 5. משימות מכירות (`sales_tasks`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| כותרת | `title` | String(300) | כן | |
| איש מכירות | `salesperson_id` | FK → salespeople | כן | |
| ליד | `lead_id` | FK → leads | לא | |
| תלמיד | `student_id` | FK → students | לא | |
| סטטוס | `status` | String(50) | כן | חדש / בטיפול / הושלם |
| תאריך יעד | `due_date` | DateTime | לא | |
| עדיפות | `priority` | Integer | לא | 0-3 |
| תיאור | `description` | Text | לא | |
| תאריך השלמה | `completed_at` | DateTime | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

**טבלת ילד — דיווחי ביצוע (`task_reports`):**

| שדה | עמודה | סוג | הערה |
|-----|-------|-----|------|
| id | `id` | PK | |
| משימה | `task_id` | FK → sales_tasks | |
| תיאור ביצוע | `description` | Text | |
| משך ביצוע | `duration` | String(100) | |
| תאריך יצירה | `created_at` | DateTime | |

---

## 6. הודעות לידים (`lead_messages`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| נושא | `subject` | String(300) | כן | |
| סטטוס | `status` | String(50) | כן | טיוטה / נשלח / נכשל |
| למי לשלוח | `recipient_type` | String(50) | לא | lead / campaign / salesperson |
| ליד ספציפי | `lead_id` | FK → leads | לא | |
| קמפיין | `campaign_id` | FK → campaigns | לא | |
| איש מכירות | `salesperson_id` | FK → salespeople | לא | |
| טלפון | `phone` | String(50) | לא | |
| צורת שליחה | `send_method` | String(50) | לא | מייל / SMS / וואצאפ |
| הודעה | `body` | Text | כן | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |
| תאריך שליחה | `sent_at` | DateTime | לא | |

---

## 7. פניות נכנסות (`inquiries`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| נושא | `subject` | String(300) | כן | |
| סוג פניה | `inquiry_type` | String(50) | כן | מייל / דואר קולי / טלפון / אחר |
| ליד מקושר | `lead_id` | FK → leads | לא | |
| תלמיד מקושר | `student_id` | FK → students | לא | |
| טלפון פונה | `phone` | String(50) | לא | |
| סטטוס | `status` | String(50) | כן | חדש / בטיפול / טופל / סגור |
| הערות | `notes` | Text | לא | |
| מי טיפל | `handled_by` | String(200) | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |
| תאריך עדכון | `updated_at` | DateTime | אוטומטי | |

**טבלת ילד — שרשור תגובות (`inquiry_responses`):**

| שדה | עמודה | סוג | הערה |
|-----|-------|-----|------|
| id | `id` | PK | |
| פניה | `inquiry_id` | FK → inquiries | |
| כותב | `author` | String(200) | |
| תוכן | `content` | Text | |
| תאריך תגובה | `created_at` | DateTime | |

---

## 8. קורסים (`courses`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| שם הקורס | `name` | String(300) | כן | |
| תאריך התחלה | `start_date` | Date | לא | |
| תאריך סיום | `end_date` | Date | לא | |
| תיאור | `description` | Text | לא | |
| סמסטר | `semester` | String(100) | לא | |
| סילבוס | `syllabus_url` | String(500) | לא | |
| קישור לאתר | `website_url` | String(500) | לא | |
| לינק זום | `zoom_url` | String(500) | לא | |
| קמפיין ימות | `yemot_campaign_id` | FK → lead_messages | לא | שיגור הודעות |
| פעיל | `is_active` | Boolean | כן | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

**מופעים מקושרים:** שיעורים/מודולים, מבחנים, תלמידים רשומים

---

## 9. שיעורים/מודולים (`course_modules`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| נושא השיעור | `name` | String(300) | כן | |
| קורס | `course_id` | FK → courses | כן | |
| מרצה | `lecturer_id` | FK → lecturers | לא | |
| סדר במודול | `module_order` | Integer | כן | |
| מספר שיעורים | `sessions_count` | Integer | לא | |
| אומדן שעות | `hours_estimate` | Numeric(5,1) | לא | |
| תאריך | `start_date` | Date | לא | |
| שעת התחלה | `start_time` | String(10) | לא | HH:MM |
| שעת סיום | `end_time` | String(10) | לא | HH:MM |
| כניסה לזום | `zoom_url` | String(500) | לא | |
| לינק הקלטה דרייב | `recording_drive_url` | String(500) | לא | |
| לינק הקלטה יוטיוב | `recording_youtube_url` | String(500) | לא | |
| לינק שאלון/מטלה | `assignment_url` | String(500) | לא | |
| פרטים נוספים | `extra_details` | Text | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

---

## 10. מרצים (`lecturers`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| שם המרצה | `name` | String(200) | כן | |
| התמחות | `specialty` | String(300) | לא | |
| טלפון | `phone` | String(50) | לא | |
| מייל | `email` | String(200) | לא | |
| הערות | `notes` | Text | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

---

## 11. מבחנים (`exams`)

> **שינוי מבני:** Exam הופך מ"ציון לתלמיד" ל"מבחן כללי" + טבלת ילד `exam_submissions` לציונים.

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| שם המבחן | `name` | String(300) | כן | |
| קורס | `course_id` | FK → courses | כן | |
| מרצה | `lecturer_id` | FK → lecturers | לא | |
| תאריך | `exam_date` | Date | לא | |
| סוג | `exam_type` | String(50) | כן | בעל-פה / בכתב / מטלה |
| לינק לשאלון | `questionnaire_url` | String(500) | לא | |
| לינק תשובות | `answers_url` | String(500) | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

**טבלת ילד — הגשות (`exam_submissions`):**

| שדה | עמודה | סוג | הערה |
|-----|-------|-----|------|
| id | `id` | PK | |
| מבחן | `exam_id` | FK → exams | |
| תלמיד | `student_id` | FK → students | |
| תאריך הגשה | `submitted_at` | DateTime | |
| ציון | `score` | Integer | |
| סטטוס | `status` | String(50) | הוגש / נבדק / עבר / נכשל |
| הערות לתלמיד | `student_notes` | Text | |
| הערה פנימית | `internal_notes` | Text | |

---

## 12. נוכחות ומטלות (`attendance`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| תלמיד | `student_id` | FK → students | כן | |
| שיעור | `module_id` | FK → course_modules | כן | |
| מרצה | `lecturer_id` | FK → lecturers | לא | |
| תאריך | `attendance_date` | Date | אוטומטי | |
| נוכחות | `is_present` | Boolean | כן | |
| מילוי מטלה | `assignment_done` | Boolean | לא | |
| ציון | `score` | Integer | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

---

## 13. תשלומים (`payments`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| אסמכתא | `reference` | String(200) | לא | נדרים פלוס |
| תלמיד | `student_id` | FK → students | לא | |
| ליד | `lead_id` | FK → leads | לא | |
| תאריך | `payment_date` | Date | כן | |
| סכום | `amount` | Numeric(10,2) | כן | |
| מטבע | `currency` | String(10) | לא | ₪ / $ |
| סוג עסקה | `transaction_type` | String(50) | לא | רגיל / הוראת קבע / החזר |
| קורס | `course_id` | FK → courses | לא | |
| מספר תשלומים | `installments` | Integer | לא | |
| יום חיוב | `charge_day` | Integer | לא | |
| צורת תשלום | `payment_method` | String(50) | לא | אשראי / העברה / מזומן |
| סטטוס | `status` | String(50) | כן | שולם / ממתין / נכשל / הוחזר |
| התחייבות | `commitment_id` | FK → commitments | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

---

## 14. התחייבויות — הוראות קבע/סליקה (`commitments`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| אסמכתא | `reference` | String(200) | לא | |
| תלמיד | `student_id` | FK → students | כן | |
| קורס | `course_id` | FK → courses | לא | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |
| תאריך סיום | `end_date` | Date | לא | |
| תשלום חודשי | `monthly_amount` | Numeric(10,2) | כן | |
| סכום כולל | `total_amount` | Numeric(10,2) | לא | |
| מספר תשלומים | `installments` | Integer | לא | |
| יום חיוב | `charge_day` | Integer | לא | |
| צורת תשלום | `payment_method` | String(50) | לא | אשראי / הוראת קבע |
| סטטוס | `status` | String(50) | כן | פעיל / מושהה / הסתיים / בוטל |

**מופעים מקושרים:** תשלומים שנוצרו מההתחייבות

---

## 15. קופונים (`coupons`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| תיאור | `description` | String(300) | כן | |
| קוד קופון | `code` | String(100) | כן | ייחודי |
| גובה הנחה | `discount_value` | Numeric(10,2) | כן | |
| סוג הנחה | `discount_type` | String(50) | כן | אחוז / סכום קבוע |
| תאריך תפוגה | `expires_at` | DateTime | לא | |
| הגבלת שימוש | `max_uses` | Integer | לא | מקסימום פעמים |
| פעיל | `is_active` | Boolean | כן | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

---

## 16. גביה (`collections`)

> **משולב עם נדרים פלוס** — כל חיוב חוזר יוצר רשומת גביה, מקושר Payment ו-Commitment.

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| תלמיד | `student_id` | FK → students | כן | |
| התחייבות | `commitment_id` | FK → commitments | לא | |
| תשלום | `payment_id` | FK → payments | לא | קישור לתשלום שנוצר |
| קורס | `course_id` | FK → courses | לא | |
| **סכום ותזמון** | | | | |
| סכום לגביה | `amount` | Numeric(10,2) | כן | |
| תאריך יעד | `due_date` | Date | כן | |
| יום חיוב | `charge_day` | Integer | לא | יום בחודש לחיוב חוזר |
| מספר תשלום | `installment_number` | Integer | לא | למשל 3 מתוך 12 |
| סה"כ תשלומים | `total_installments` | Integer | לא | |
| **סטטוס** | | | | |
| סטטוס | `status` | String(50) | כן | ממתין / נגבה / נכשל / בוטל |
| ניסיונות גביה | `attempts` | Integer | אוטומטי | default: 0 |
| תאריך גביה בפועל | `collected_at` | DateTime | לא | |
| אסמכתא | `reference` | String(200) | לא | |
| הערות | `notes` | Text | לא | |
| **אינטגרציית נדרים פלוס** | | | | |
| מזהה תרומה נדרים | `nedarim_donation_id` | String(50) | לא | DON_xxxxx |
| מזהה עסקה נדרים | `nedarim_transaction_id` | String(50) | לא | TRX_xxxxx |
| מזהה הוראת קבע | `nedarim_subscription_id` | String(50) | לא | מ-Commitment |
| **מטא** | | | | |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

**מופעים מקושרים:**
- תלמיד (`students`) — פרטי התלמיד
- התחייבות (`commitments`) — הוראת הקבע שיצרה את הגביה
- תשלום (`payments`) — התשלום שנוצר לאחר גביה מוצלחת

---

## 17. הוצאות (`expenses`)

| שדה | עמודה | סוג | חובה | הערה |
|-----|-------|-----|------|------|
| id | `id` | PK | אוטומטי | |
| ספק | `vendor` | String(300) | כן | |
| תאריך | `expense_date` | Date | כן | |
| סכום | `amount` | Numeric(10,2) | כן | |
| פירוט | `description` | Text | לא | |
| קורס | `course_id` | FK → courses | לא | |
| קמפיין | `campaign_id` | FK → campaigns | לא | |
| צורת תשלום | `payment_method` | String(50) | לא | |
| חשבונית | `invoice_file` | String(500) | לא | נתיב/URL לקובץ |
| תאריך יצירה | `created_at` | DateTime | אוטומטי | |

---

## ישויות 18–21 (לאפיון בהמשך)

| # | ישות | תיאור |
|---|------|--------|
| 18 | משימות כלליות | ניהול משימות פנימיות שלא קשורות למכירות |
| 19 | פרויקטים | ניהול פרויקטים |
| 20 | יעדים | הגדרת יעדים ומעקב |
| 21 | שיגור הודעות + לוג | שיגור מרוכז ולוג תוצאות |

---

## אינדקסים מרכזיים

```
leads:         phone (unique), status, salesperson_id, campaign_id
students:      phone, status, lead_id
payments:      student_id, status, commitment_id
enrollments:   student_id, course_id
attendance:    student_id, module_id
exams:         course_id
exam_submissions: exam_id, student_id
sales_tasks:   salesperson_id, status, lead_id
inquiries:     status, lead_id, student_id
collections:   student_id, status, due_date
commitments:   student_id, status
```
