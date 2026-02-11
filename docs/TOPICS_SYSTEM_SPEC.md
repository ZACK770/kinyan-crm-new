# אפיון מערכת ניהול נושאים (Topics) וקורסים עם נקודות כניסה

## 1. סקירה כללית

### 1.1 מטרת המערכת
מערכת לניהול קורסים מבוססי נושאים (Topics/Semesters) עם לופ אינסופי, נקודות כניסה דינמיות, ומעקב אוטומטי אחר התקדמות תלמידים.

### 1.2 עקרונות מרכזיים
- **קורס** = אוסף של נושאים (Topics) בסדר מסוים
- **נושא** (Topic) = אוסף של מפגשים (Lessons) בסדר מסוים
- **לופ אינסופי** = הנושאים חוזרים על עצמם ללא סוף
- **נקודת כניסה** = המפגש הבא שבו תלמיד חדש יכול להצטרף
- **מחזור** = מעבר על כל הנושאים פעם אחת
- **בוגר** = תלמיד שסיים מחזור שלם

---

## 2. מבנה נתונים (Database Schema)

### 2.1 טבלאות קיימות (לעדכון)

#### `courses` (קיים - להרחבה)
```sql
-- שדות קיימים
id, name, description, status, created_at, updated_at

-- שדות חדשים להוסיף:
topics_loop_enabled BOOLEAN DEFAULT TRUE  -- האם הקורס במצב לופ אינסופי
topics_order JSONB  -- מערך של topic_ids בסדר הנכון: [1,2,3,4]
```

#### `students` (קיים - להרחבה)
```sql
-- שדות קיימים
id, full_name, email, phone, status, created_at, updated_at

-- שדות חדשים להוסיף:
entry_point_lesson_id INTEGER  -- המפגש שבו התלמיד התחיל
entry_date DATE  -- תאריך כניסה בפועל
graduation_date DATE  -- תאריך סיום מחושב (NULL אם עדיין פעיל)
is_graduate BOOLEAN DEFAULT FALSE  -- האם סיים מחזור שלם
```

### 2.2 טבלאות חדשות

#### `topics` (חדש)
```sql
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,  -- שם הנושא (לדוגמה: "הלכות שבת")
    description TEXT,
    order_index INTEGER NOT NULL,  -- מיקום בסדר הנושאים (0,1,2,3...)
    lessons_count INTEGER DEFAULT 0,  -- מספר מפגשים בנושא
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(course_id, order_index)
);

CREATE INDEX idx_topics_course ON topics(course_id);
```

#### `lessons` (חדש - מחליף את sessions הקיימות)
```sql
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    
    -- פרטי מפגש
    lesson_number INTEGER NOT NULL,  -- מספר המפגש בתוך הנושא (1,2,3...)
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- תוכן
    video_url VARCHAR(500),  -- קישור להקלטה
    video_duration INTEGER,  -- אורך בשניות
    cover_image_url VARCHAR(500),  -- תמונת כיסוי
    lecturer_name VARCHAR(255),  -- שם המרצה
    
    -- מטלה
    assignment_title VARCHAR(255),
    assignment_description TEXT,
    assignment_file_url VARCHAR(500),
    assignment_due_days INTEGER DEFAULT 7,  -- כמה ימים להגשה
    
    -- תאריכים
    scheduled_date TIMESTAMP,  -- מתי השיעור מתוכנן
    actual_date TIMESTAMP,  -- מתי השיעור התקיים בפועל
    
    -- סטטוס
    status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled/completed/cancelled
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(topic_id, lesson_number)
);

CREATE INDEX idx_lessons_topic ON lessons(topic_id);
CREATE INDEX idx_lessons_course ON lessons(course_id);
CREATE INDEX idx_lessons_scheduled ON lessons(scheduled_date);
```

#### `student_lesson_progress` (חדש)
```sql
CREATE TABLE student_lesson_progress (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    
    -- נוכחות
    attended BOOLEAN DEFAULT FALSE,
    attendance_date TIMESTAMP,
    
    -- צפייה בהקלטה
    video_watched BOOLEAN DEFAULT FALSE,
    video_watch_percentage INTEGER DEFAULT 0,  -- 0-100
    last_watched_at TIMESTAMP,
    
    -- מטלה
    assignment_submitted BOOLEAN DEFAULT FALSE,
    assignment_file_url VARCHAR(500),
    assignment_submitted_at TIMESTAMP,
    assignment_grade INTEGER,  -- ציון 0-100
    assignment_feedback TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(student_id, lesson_id)
);

CREATE INDEX idx_progress_student ON student_lesson_progress(student_id);
CREATE INDEX idx_progress_lesson ON student_lesson_progress(lesson_id);
```

#### `course_entry_points` (חדש - view מחושב)
```sql
-- View שמחשב נקודות כניסה זמינות לכל קורס
CREATE VIEW course_entry_points AS
SELECT 
    c.id as course_id,
    c.name as course_name,
    l.id as lesson_id,
    l.title as lesson_title,
    l.scheduled_date as entry_date,
    t.name as topic_name,
    l.lesson_number,
    -- חישוב כמה מפגשים נותרו עד סוף הנושא
    (SELECT COUNT(*) FROM lessons WHERE topic_id = t.id AND lesson_number > l.lesson_number) as lessons_until_topic_end
FROM courses c
JOIN topics t ON t.course_id = c.id
JOIN lessons l ON l.topic_id = t.id
WHERE l.scheduled_date > NOW()
ORDER BY c.id, l.scheduled_date;
```

---

## 3. לוגיקה עסקית (Business Logic)

### 3.1 חישוב נקודת כניסה

#### אלגוריתם: מציאת נקודת כניסה הבאה
```python
def get_next_entry_point(course_id: int, city: str = None) -> dict:
    """
    מחזיר את נקודת הכניסה הבאה לקורס.
    
    נקודת כניסה = המפגש הבא שמתחיל נושא חדש
    """
    # 1. מצא את הנושא הנוכחי שרץ עכשיו
    current_topic = get_current_running_topic(course_id, city)
    
    # 2. מצא את המפגש הנוכחי בנושא
    current_lesson = get_current_lesson_in_topic(current_topic.id)
    
    # 3. חשב כמה מפגשים נותרו עד סוף הנושא
    lessons_remaining = count_lessons_remaining_in_topic(
        current_topic.id, 
        current_lesson.lesson_number
    )
    
    # 4. הנושא הבא בלופ
    next_topic = get_next_topic_in_loop(course_id, current_topic.order_index)
    
    # 5. המפגש הראשון של הנושא הבא
    next_entry_lesson = get_first_lesson_of_topic(next_topic.id)
    
    # 6. חשב תאריך כניסה משוער
    estimated_entry_date = calculate_entry_date(
        current_lesson.scheduled_date,
        lessons_remaining
    )
    
    return {
        "entry_lesson_id": next_entry_lesson.id,
        "entry_date": estimated_entry_date,
        "topic_name": next_topic.name,
        "lessons_until_entry": lessons_remaining,
        "current_topic": current_topic.name,
        "current_lesson_number": current_lesson.lesson_number
    }
```

### 3.2 חישוב סטטוס תלמיד (פעיל/בוגר)

#### אלגוריתם: בדיקה האם תלמיד סיים מחזור
```python
def calculate_student_status(student_id: int) -> dict:
    """
    בודק האם תלמיד סיים מחזור שלם של הקורס.
    """
    student = get_student(student_id)
    course = get_student_course(student_id)
    
    # 1. מצא את נקודת הכניסה של התלמיד
    entry_lesson = get_lesson(student.entry_point_lesson_id)
    entry_topic = get_topic(entry_lesson.topic_id)
    
    # 2. בנה רשימת כל הנושאים שהתלמיד צריך לעבור
    topics_order = get_course_topics_order(course.id)
    entry_index = entry_topic.order_index
    
    # רשימה מסודרת מנקודת הכניסה
    required_topics = (
        topics_order[entry_index:] +  # מנקודת הכניסה עד הסוף
        topics_order[:entry_index]     # מההתחלה עד נקודת הכניסה
    )
    
    # 3. בדוק כמה נושאים התלמיד השלים
    completed_topics = []
    for topic_id in required_topics:
        if is_topic_completed_by_student(student_id, topic_id):
            completed_topics.append(topic_id)
        else:
            break  # עצר ברגע שמצאת נושא שלא הושלם
    
    # 4. חשב אחוז התקדמות
    progress_percentage = (len(completed_topics) / len(required_topics)) * 100
    
    # 5. קבע סטטוס
    is_graduate = len(completed_topics) == len(required_topics)
    
    return {
        "is_graduate": is_graduate,
        "progress_percentage": progress_percentage,
        "completed_topics": len(completed_topics),
        "total_topics": len(required_topics),
        "current_topic": required_topics[len(completed_topics)] if not is_graduate else None
    }

def is_topic_completed_by_student(student_id: int, topic_id: int) -> bool:
    """
    בודק האם תלמיד השלים נושא (נכח/צפה ב-80%+ מהמפגשים).
    """
    lessons = get_lessons_in_topic(topic_id)
    progress_records = get_student_progress_for_lessons(student_id, [l.id for l in lessons])
    
    completed_count = sum(
        1 for p in progress_records 
        if p.attended or p.video_watch_percentage >= 80
    )
    
    return completed_count >= (len(lessons) * 0.8)  # 80% threshold
```

### 3.3 ניהול סדר נושאים

#### אלגוריתם: שינוי סדר נושאים (Drag & Drop)
```python
def reorder_topics(course_id: int, new_order: list[int]) -> bool:
    """
    משנה את סדר הנושאים בקורס.
    
    Args:
        course_id: מזהה הקורס
        new_order: רשימת topic_ids בסדר החדש [3, 1, 4, 2]
    
    Returns:
        True אם הצליח, False אם נכשל
    """
    # 1. ולידציה - וודא שכל הנושאים שייכים לקורס
    existing_topics = get_course_topics(course_id)
    if set(new_order) != set(t.id for t in existing_topics):
        raise ValueError("Invalid topic IDs in new order")
    
    # 2. עדכן את order_index לכל נושא
    for index, topic_id in enumerate(new_order):
        update_topic_order(topic_id, index)
    
    # 3. עדכן את topics_order בטבלת courses
    update_course_topics_order(course_id, new_order)
    
    # 4. רענן את נקודות הכניסה המחושבות
    refresh_entry_points_cache(course_id)
    
    return True
```

---

## 4. API Endpoints

### 4.1 Topics Management

#### `GET /api/courses/{course_id}/topics`
```json
// Response
{
  "success": true,
  "topics": [
    {
      "id": 1,
      "name": "הלכות שבת",
      "order_index": 0,
      "lessons_count": 12,
      "first_lesson": {
        "id": 101,
        "title": "מבוא להלכות שבת",
        "scheduled_date": "2026-03-01T19:00:00Z"
      }
    }
  ]
}
```

#### `POST /api/courses/{course_id}/topics/reorder`
```json
// Request
{
  "new_order": [3, 1, 4, 2]  // topic IDs בסדר החדש
}

// Response
{
  "success": true,
  "message": "Topics reordered successfully"
}
```

#### `GET /api/topics/{topic_id}/lessons`
```json
// Response
{
  "success": true,
  "topic": {
    "id": 1,
    "name": "הלכות שבת",
    "course_name": "הלכה למעשה"
  },
  "lessons": [
    {
      "id": 101,
      "lesson_number": 1,
      "title": "מבוא להלכות שבת",
      "scheduled_date": "2026-03-01T19:00:00Z",
      "video_url": "https://...",
      "lecturer_name": "הרב כהן",
      "students_count": 45,
      "assignment": {
        "title": "מטלה 1",
        "submitted_count": 32,
        "total_students": 45
      }
    }
  ]
}
```

### 4.2 Entry Points

#### `GET /api/courses/{course_id}/entry-points`
```json
// Query params: ?city=ירושלים
// Response
{
  "success": true,
  "current_status": {
    "current_topic": "הלכות שבת",
    "current_lesson_number": 5,
    "lessons_remaining_in_topic": 7
  },
  "next_entry_point": {
    "entry_lesson_id": 201,
    "entry_date": "2026-04-15T19:00:00Z",
    "topic_name": "הלכות תפילה",
    "lessons_until_entry": 7
  }
}
```

### 4.3 Student Progress

#### `GET /api/students/{student_id}/progress`
```json
// Response
{
  "success": true,
  "student": {
    "id": 123,
    "full_name": "משה כהן",
    "entry_date": "2025-09-01",
    "entry_topic": "הלכות שבת"
  },
  "progress": {
    "is_graduate": false,
    "progress_percentage": 65.5,
    "completed_topics": 5,
    "total_topics": 8,
    "current_topic": {
      "id": 3,
      "name": "הלכות תפילה",
      "completed_lessons": 8,
      "total_lessons": 12
    }
  },
  "recent_lessons": [
    {
      "lesson_id": 305,
      "title": "דיני קריאת שמע",
      "attended": true,
      "assignment_submitted": true,
      "assignment_grade": 95
    }
  ]
}
```

#### `POST /api/students/{student_id}/lessons/{lesson_id}/progress`
```json
// Request - עדכון התקדמות
{
  "attended": true,
  "video_watch_percentage": 100,
  "assignment_submitted": true,
  "assignment_file_url": "https://..."
}

// Response
{
  "success": true,
  "progress_updated": true
}
```

### 4.4 Lesson Workspace

#### `GET /api/lessons/{lesson_id}/workspace`
```json
// Response - כל המידע למפגש
{
  "success": true,
  "lesson": {
    "id": 305,
    "title": "דיני קריאת שמע",
    "topic_name": "הלכות תפילה",
    "course_name": "הלכה למעשה",
    "lesson_number": 5,
    "scheduled_date": "2026-03-15T19:00:00Z",
    "video_url": "https://...",
    "video_duration": 5400,
    "lecturer_name": "הרב כהן",
    "cover_image_url": "https://..."
  },
  "assignment": {
    "title": "מטלה 5",
    "description": "סכמו את עיקרי ההלכות...",
    "file_url": "https://...",
    "due_days": 7,
    "submitted_count": 32,
    "total_students": 45
  },
  "students": [
    {
      "student_id": 123,
      "full_name": "משה כהן",
      "attended": true,
      "video_watched": true,
      "assignment_submitted": true,
      "assignment_grade": 95
    }
  ]
}
```

#### `PUT /api/lessons/{lesson_id}`
```json
// Request - עדכון פרטי מפגש
{
  "video_url": "https://new-recording.com/...",
  "assignment_title": "מטלה מעודכנת",
  "actual_date": "2026-03-15T19:30:00Z"
}
```

---

## 5. ממשקי משתמש (UI/UX)

### 5.1 ממשק ניהול קורס (Admin)

#### עמוד: `/courses/{course_id}`

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ קורס: הלכה למעשה                      [⚙️ הגדרות]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📊 סטטיסטיקות                                       │
│ ┌──────────┬──────────┬──────────┬──────────┐      │
│ │ תלמידים  │ נושאים   │ מפגשים   │ בוגרים   │      │
│ │   145    │    8     │   96     │   23     │      │
│ └──────────┴──────────┴──────────┴──────────┘      │
│                                                     │
│ 📚 נושאים (ניתן לגרור ולשנות סדר)                  │
│ ┌─────────────────────────────────────────────┐    │
│ │ ☰ 1. הלכות שבת (12 מפגשים)         [👁️]    │    │
│ │ ☰ 2. הלכות תפילה (15 מפגשים)       [👁️]    │    │
│ │ ☰ 3. הלכות כשרות (10 מפגשים)       [👁️]    │    │
│ │ ☰ 4. הלכות ברכות (8 מפגשים)        [👁️]    │    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ 👥 תלמידים פעילים (145)                            │
│ [סינון: הכל ▼] [חיפוש...]                          │
│ ┌─────────────────────────────────────────────┐    │
│ │ משה כהן | נושא נוכחי: הלכות תפילה | 65%    │    │
│ │ דוד לוי | נושא נוכחי: הלכות שבת | 30%      │    │
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**פיצ'רים:**
- ✅ Drag & Drop לשינוי סדר נושאים
- ✅ לחיצה על נושא → מעבר לעמוד הנושא
- ✅ רשימת תלמידים עם סינון לפי נושא נוכחי
- ✅ אחוז התקדמות לכל תלמיד
- ❌ לא ניתן להוסיף/למחוק נושאים מכאן

### 5.2 ממשק ניהול נושא (Admin)

#### עמוד: `/topics/{topic_id}`

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ ← חזרה לקורס                                        │
│ נושא: הלכות שבת | קורס: הלכה למעשה                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📅 מפגשים (12)                                      │
│ ┌─────────────────────────────────────────────┐    │
│ │ 📹 מפגש 1: מבוא להלכות שבת                  │    │
│ │    📅 01/03/2026 19:00 | 👥 45 תלמידים       │    │
│ │    📝 מטלה: 32/45 הוגשו                     │    │
│ │    [פתח Workspace]                          │    │
│ ├─────────────────────────────────────────────┤    │
│ │ 📹 מפגש 2: 39 מלאכות                        │    │
│ │    📅 08/03/2026 19:00 | 👥 43 תלמידים       │    │
│ │    📝 מטלה: 28/43 הוגשו                     │    │
│ │    [פתח Workspace]                          │    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ 👥 תלמידים בנושא זה (45)                           │
│ [רשימת תלמידים שנמצאים בנושא הזה]                  │
└─────────────────────────────────────────────────────┘
```

### 5.3 Lesson Workspace (Admin)

#### עמוד: `/lessons/{lesson_id}/workspace`

**Tabs:**
1. **פרטי מפגש** - עריכת כל הפרטים
2. **תלמידים** - רשימת תלמידים + נוכחות
3. **מטלה** - העלאת מטלה וצפייה בהגשות

**Tab 1: פרטי מפגש**
```
┌─────────────────────────────────────────────────────┐
│ [Tab: פרטי מפגש] [Tab: תלמידים] [Tab: מטלה]        │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📝 עריכת פרטי מפגש                                  │
│ ┌─────────────────────────────────────────────┐    │
│ │ כותרת: [מבוא להלכות שבת____________]        │    │
│ │ תיאור: [________________________]           │    │
│ │ מרצה: [הרב כהן___________________]          │    │
│ │ תאריך: [01/03/2026] [19:00]                 │    │
│ │                                             │    │
│ │ 🎥 הקלטה                                     │    │
│ │ קישור: [https://...____________]            │    │
│ │ תמונת כיסוי: [📤 העלה תמונה]                │    │
│ │                                             │    │
│ │ [💾 שמור שינויים]                           │    │
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Tab 2: תלמידים**
```
┌─────────────────────────────────────────────────────┐
│ [Tab: פרטי מפגש] [Tab: תלמידים] [Tab: מטלה]        │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 👥 תלמידים (45)                                     │
│ [חיפוש...] [סנן: הכל ▼]                            │
│ ┌─────────────────────────────────────────────┐    │
│ │ ☑️ משה כהן | נוכח | צפה 100% | הגיש מטלה    │    │
│ │ ☐ דוד לוי | לא נוכח | צפה 45% | לא הגיש    │    │
│ │ ☑️ שרה כהן | נוכחה | צפה 100% | הגישה       │    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ [📥 ייצא לאקסל] [✉️ שלח תזכורת לכל מי שלא הגיש]    │
└─────────────────────────────────────────────────────┘
```

**Tab 3: מטלה**
```
┌─────────────────────────────────────────────────────┐
│ [Tab: פרטי מפגש] [Tab: תלמידים] [Tab: מטלה]        │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📝 מטלה                                             │
│ ┌─────────────────────────────────────────────┐    │
│ │ כותרת: [מטלה 1: סיכום הלכות שבת_____]      │    │
│ │ הוראות: [________________________]          │    │
│ │ קובץ מטלה: [📤 העלה PDF]                    │    │
│ │ מועד הגשה: [7] ימים מתאריך השיעור           │    │
│ │                                             │    │
│ │ [💾 שמור]                                    │    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ 📊 הגשות (32/45)                                    │
│ ┌─────────────────────────────────────────────┐    │
│ │ משה כהן | הוגש 02/03 | [📄 צפה] [✏️ ציון]  │    │
│ │ שרה כהן | הוגש 03/03 | [📄 צפה] [✏️ ציון]  │    │
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 5.4 ממשק תלמיד (Student Portal)

#### עמוד: `/student/my-course`

**Layout מעוצב:**
```
┌─────────────────────────────────────────────────────┐
│ 🎓 הקורס שלי: הלכה למעשה                            │
│ התקדמות: ████████░░ 65%                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📚 הנושא הנוכחי שלי: הלכות תפילה                    │
│                                                     │
│ ┌───────────────────────────────────────────┐      │
│ │ 🎬 מפגש 8: דיני קריאת שמע                 │      │
│ │ ┌─────────────────────────────────────┐   │      │
│ │ │ [תמונת כיסוי - הרב כהן]             │   │      │
│ │ └─────────────────────────────────────┘   │      │
│ │ 👨‍🏫 הרב כהן | ⏱️ 90 דקות                 │      │
│ │ 📅 15/03/2026 19:00                       │      │
│ │                                           │      │
│ │ [▶️ צפה בהקלטה] [📝 הגש מטלה]            │      │
│ └───────────────────────────────────────────┘      │
│                                                     │
│ 📋 המפגשים הבאים                                    │
│ ┌───────────────────────────────────────────┐      │
│ │ 🔒 מפגש 9: הלכות תפילה בציבור            │      │
│ │    📅 22/03/2026 19:00                    │      │
│ └───────────────────────────────────────────┘      │
│                                                     │
│ ✅ מפגשים שצפיתי (32)                               │
│ [הצג היסטוריה]                                     │
└─────────────────────────────────────────────────────┘
```

**Sidebar (רשימת מפגשים):**
```
┌──────────────────┐
│ 📚 נושאים        │
├──────────────────┤
│ ✅ הלכות שבת     │
│    12/12 ✓       │
│                  │
│ 🔄 הלכות תפילה   │
│    8/15 ⏳       │
│                  │
│ 🔒 הלכות כשרות   │
│    0/10          │
└──────────────────┘
```

#### עמוד מפגש: `/student/lessons/{lesson_id}`

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ ← חזרה לקורס                                        │
│ מפגש 8: דיני קריאת שמע                              │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 🎥 וידאו                                            │
│ ┌─────────────────────────────────────────────┐    │
│ │ [נגן וידאו - 90 דקות]                       │    │
│ │ ▶️ ⏸️ ⏭️ 🔊 ⚙️                                │    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ 📝 מטלה: סיכום דיני קריאת שמע                      │
│ ┌─────────────────────────────────────────────┐    │
│ │ הוראות: סכמו את עיקרי ההלכות...           │    │
│ │                                             │    │
│ │ [📥 הורד קובץ מטלה]                         │    │
│ │                                             │    │
│ │ 📤 הגשת מטלה                                │    │
│ │ [בחר קובץ...] [📤 העלה]                     │    │
│ │                                             │    │
│ │ ⏰ מועד הגשה: 22/03/2026                     │    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ ✅ סטטוס: צפית במפגש | הגשת מטלה                   │
└─────────────────────────────────────────────────────┘
```

---

## 6. תהליכי עבודה (Workflows)

### 6.1 תהליך הוספת תלמיד חדש

```
1. איש מכירות מקבל ליד
   ↓
2. בודק עיר + קורס רצוי
   ↓
3. מערכת מציגה: "נקודת כניסה הבאה: 15/04/2026 - נושא: הלכות תפילה"
   ↓
4. איש מכירות מאשר → ליד הופך לתלמיד
   ↓
5. מערכת שומרת:
   - entry_point_lesson_id = 201
   - entry_date = 2026-04-15
   ↓
6. תלמיד מקבל הודעת ברוכים הבאים + קישור למערכת למידה
```

### 6.2 תהליך מעקב אחר התקדמות

```
כל שבוע (Cron Job):
1. עבור על כל התלמידים הפעילים
   ↓
2. לכל תלמיד:
   - חשב כמה נושאים הושלמו
   - בדוק אם הושלם מחזור שלם
   ↓
3. אם הושלם מחזור:
   - is_graduate = TRUE
   - graduation_date = NOW()
   - שלח מייל מזל טוב
   ↓
4. אם לא הושלם:
   - עדכן progress_percentage
   - אם אחוז נמוך → שלח תזכורת
```

### 6.3 תהליך שינוי סדר נושאים

```
1. Admin נכנס לעמוד קורס
   ↓
2. גורר נושא למיקום חדש
   ↓
3. מערכת:
   - עדכן order_index לכל הנושאים
   - עדכן topics_order בקורס
   - רענן cache של נקודות כניסה
   ↓
4. ⚠️ אזהרה: "שינוי זה לא ישפיע על תלמידים קיימים"
```

---

## 7. שיקולים טכניים

### 7.1 Performance

**Caching:**
- נקודות כניסה → Redis (TTL: 1 hour)
- סטטוס תלמידים → Redis (TTL: 30 minutes)
- רשימת נושאים → Redis (TTL: 24 hours)

**Indexes:**
```sql
CREATE INDEX idx_lessons_scheduled ON lessons(scheduled_date);
CREATE INDEX idx_progress_student_lesson ON student_lesson_progress(student_id, lesson_id);
CREATE INDEX idx_topics_course_order ON topics(course_id, order_index);
```

### 7.2 Data Integrity

**Constraints:**
- לא ניתן למחוק נושא אם יש לו מפגשים
- לא ניתן למחוק מפגש אם יש לו התקדמות תלמידים
- order_index חייב להיות ייחודי בתוך קורס

### 7.3 Background Jobs

**Daily Jobs:**
1. חישוב סטטוס בוגרים (02:00)
2. שליחת תזכורות למטלות (10:00)
3. ניקוי cache ישן (03:00)

**Weekly Jobs:**
1. דוח התקדמות למנהלים (ראשון 08:00)
2. סטטיסטיקות למרצים (ראשון 09:00)

---

## 8. מסמכי עזר

### 8.1 טרמינולוגיה

| מונח באנגלית | מונח בעברית | הסבר |
|-------------|------------|------|
| Course | קורס | אוסף נושאים |
| Topic/Semester | נושא | אוסף מפגשים |
| Lesson | מפגש | שיעור בודד |
| Entry Point | נקודת כניסה | המפגש הראשון לתלמיד חדש |
| Loop | לופ | חזרה על הנושאים |
| Cycle | מחזור | מעבר על כל הנושאים פעם אחת |
| Graduate | בוגר | תלמיד שסיים מחזור |

### 8.2 דוגמה מלאה

**קורס: "הלכה למעשה"**

נושאים (Topics):
1. הלכות שבת (12 מפגשים)
2. הלכות תפילה (15 מפגשים)
3. הלכות כשרות (10 מפגשים)
4. הלכות ברכות (8 מפגשים)

**סה"כ: 45 מפגשים במחזור**

**תלמיד: משה כהן**
- נקודת כניסה: מפגש 1 של "הלכות תפילה" (01/03/2026)
- מחזור שלו: תפילה → כשרות → ברכות → שבת
- סה"כ מפגשים: 15+10+8+12 = 45
- התקדמות נוכחית: 30 מפגשים (66%)
- סטטוס: פעיל

---

## 9. סיכום והמלצות יישום

### 9.1 שלבי פיתוח מומלצים

**Phase 1: Foundation (2-3 שבועות)**
1. ✅ יצירת טבלאות חדשות (topics, lessons, student_lesson_progress)
2. ✅ Migration של נתונים קיימים
3. ✅ API endpoints בסיסיים

**Phase 2: Core Logic (2-3 שבועות)**
1. ✅ אלגוריתם חישוב נקודות כניסה
2. ✅ אלגוריתם חישוב סטטוס תלמידים
3. ✅ ניהול סדר נושאים (Drag & Drop)

**Phase 3: Admin UI (2 שבועות)**
1. ✅ עמוד ניהול קורס
2. ✅ עמוד ניהול נושא
3. ✅ Lesson Workspace

**Phase 4: Student Portal (2 שבועות)**
1. ✅ ממשק תלמיד מעוצב
2. ✅ נגן וידאו
3. ✅ הגשת מטלות

**Phase 5: Automation (1 שבוע)**
1. ✅ Background jobs
2. ✅ Notifications
3. ✅ Reports

### 9.2 נקודות קריטיות

⚠️ **חשוב:**
- אין למחוק או לערוך נושאים אחרי שיש תלמידים
- שינוי סדר נושאים לא משפיע על תלמידים קיימים
- נקודת כניסה נקבעת פעם אחת ולא משתנה

✅ **Best Practices:**
- Cache נקודות כניסה לביצועים
- Background jobs לחישובים כבדים
- Audit log לכל שינוי בסדר נושאים

---

**סוף מסמך אפיון**
