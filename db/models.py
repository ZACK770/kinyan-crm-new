"""
All SQLAlchemy models in one place.
Maps directly to PostgreSQL tables.
Full spec: ENTITIES_SPEC.md (17 entities + child tables)
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, Numeric, Boolean, Date, DateTime,
    ForeignKey, Index, UniqueConstraint, ARRAY, LargeBinary, func, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base


# ============================================================
# User (משתמשי מערכת) — הרשאות ואימות
# ============================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(300), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(500))  # null if Google-only
    google_id: Mapped[Optional[str]] = mapped_column(String(200), unique=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Permission level: 0=pending, 10=viewer, 20=editor, 30=manager, 35=class_manager, 40=admin
    permission_level: Mapped[int] = mapped_column(Integer, default=0)
    role_name: Mapped[str] = mapped_column(String(50), default="pending")  # pending/viewer/editor/manager/class_manager/admin

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_google_id", "google_id"),
    )


# ============================================================
# EntityPermission (הרשאות לפי ישות) — מגדיר רמת הרשאה נדרשת לכל ישות
# ============================================================
class EntityPermission(Base):
    __tablename__ = "entity_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "leads", "students"
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # "view" / "create" / "edit" / "delete"
    required_level: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    __table_args__ = (
        UniqueConstraint("entity_name", "action", name="uq_entity_action"),
        Index("idx_entity_perm_name", "entity_name"),
    )


# ============================================================
# Salespeople (אנשי מכירות) — entity 4
# ============================================================
class Salesperson(Base):
    __tablename__ = "salespeople"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)  # Link to system user
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    ref_code: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Notification settings
    notification_webhook_url: Mapped[Optional[str]] = mapped_column(String(500))  # External webhook URL (WhatsApp API, etc.)
    notify_on_new_lead: Mapped[bool] = mapped_column(Boolean, default=True)  # Send notification when new lead assigned

    # Relations
    user: Mapped[Optional["User"]] = relationship()
    leads: Mapped[List["Lead"]] = relationship(back_populates="salesperson")
    tasks: Mapped[List["SalesTask"]] = relationship(back_populates="salesperson")
    campaign_links: Mapped[List["CampaignSalespersonLink"]] = relationship(back_populates="salesperson")
    assignment_rules: Mapped[Optional["SalesAssignmentRules"]] = relationship(back_populates="salesperson", uselist=False)


# ============================================================
# SalesAssignmentRules (כללי שיוך לידים) — smart lead assignment
# ============================================================
class SalesAssignmentRules(Base):
    __tablename__ = "sales_assignment_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    salesperson_id: Mapped[int] = mapped_column(ForeignKey("salespeople.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Daily limits
    daily_lead_limit: Mapped[Optional[int]] = mapped_column(Integer)  # NULL = unlimited
    daily_leads_assigned: Mapped[int] = mapped_column(Integer, default=0)
    last_reset_date: Mapped[Optional[date]] = mapped_column(Date)

    # Priority/preference weight (1-10, higher = more leads)
    priority_weight: Mapped[int] = mapped_column(Integer, default=1)

    # Workload control
    max_open_leads: Mapped[Optional[int]] = mapped_column(Integer)  # NULL = unlimited
    status_filters: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=["ליד חדש", "במעקב", "מתעניין"])

    # Active/inactive
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_assignment_rules_salesperson", "salesperson_id"),
        Index("idx_assignment_rules_active", "is_active"),
    )

    salesperson: Mapped["Salesperson"] = relationship(back_populates="assignment_rules")


# ============================================================
# Campaigns (קמפיינים) — entity 3
# ============================================================
class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    campaign_type: Mapped[Optional[str]] = mapped_column(String(100))
    platforms: Mapped[Optional[str]] = mapped_column(Text)  # comma-separated: פייסבוק, גוגל, ימות
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    form_name: Mapped[Optional[str]] = mapped_column(String(300))
    landing_page_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    leads: Mapped[List["Lead"]] = relationship(back_populates="campaign")
    course: Mapped[Optional["Course"]] = relationship(back_populates="campaigns")
    salesperson_links: Mapped[List["CampaignSalespersonLink"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")
    landing_links: Mapped[List["CampaignLandingLink"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")


# ============================================================
# CampaignSalespersonLink (לינקים לאנשי מכירות בקמפיין)
# ============================================================
class CampaignSalespersonLink(Base):
    __tablename__ = "campaign_salesperson_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    salesperson_id: Mapped[int] = mapped_column(ForeignKey("salespeople.id"), nullable=False)
    message_text: Mapped[Optional[str]] = mapped_column(Text)

    campaign: Mapped["Campaign"] = relationship(back_populates="salesperson_links")
    salesperson: Mapped["Salesperson"] = relationship(back_populates="campaign_links")


# ============================================================
# CampaignLandingLink (לינקים לדף נחיתה בקמפיין)
# ============================================================
class CampaignLandingLink(Base):
    __tablename__ = "campaign_landing_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    source_label: Mapped[Optional[str]] = mapped_column(String(200))  # UTM source
    url_with_source: Mapped[Optional[str]] = mapped_column(String(500))

    campaign: Mapped["Campaign"] = relationship(back_populates="landing_links")


# ============================================================
# Products table removed - pricing moved to Course model
# ============================================================


# ============================================================
# Courses (קורסים) — entity 8
# ============================================================
class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    semester: Mapped[Optional[str]] = mapped_column(String(100))
    syllabus_url: Mapped[Optional[str]] = mapped_column(String(500))
    website_url: Mapped[Optional[str]] = mapped_column(String(500))
    zoom_url: Mapped[Optional[str]] = mapped_column(String(500))
    total_sessions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Pricing (was in Product table)
    price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    payments_count: Mapped[int] = mapped_column(Integer, default=1)
    
    # Topics system (new)
    topics_loop_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    topics_order: Mapped[Optional[str]] = mapped_column(Text)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    modules: Mapped[List["CourseModule"]] = relationship(back_populates="course", order_by="CourseModule.module_order")
    tracks: Mapped[List["CourseTrack"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="course")
    campaigns: Mapped[List["Campaign"]] = relationship(back_populates="course")
    exams: Mapped[List["Exam"]] = relationship(back_populates="course")


# ============================================================
# CourseModules (שיעורים/מודולים) — entity 9
# ============================================================
class CourseModule(Base):
    __tablename__ = "course_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecturers.id"))
    module_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_count: Mapped[Optional[int]] = mapped_column(Integer)
    hours_estimate: Mapped[Optional[Numeric]] = mapped_column(Numeric(5, 1))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    start_time: Mapped[Optional[str]] = mapped_column(String(10))   # HH:MM
    end_time: Mapped[Optional[str]] = mapped_column(String(10))     # HH:MM
    zoom_url: Mapped[Optional[str]] = mapped_column(String(500))
    recording_drive_url: Mapped[Optional[str]] = mapped_column(String(500))
    recording_youtube_url: Mapped[Optional[str]] = mapped_column(String(500))
    assignment_url: Mapped[Optional[str]] = mapped_column(String(500))
    extra_details: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("course_id", "module_order", name="uq_course_module_order"),
        Index("idx_modules_course", "course_id"),
    )

    course: Mapped["Course"] = relationship(back_populates="modules")
    lecturer: Mapped[Optional["Lecturer"]] = relationship(back_populates="modules")


# ============================================================
# Lecturers (מרצים) — entity 10
# ============================================================
class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    specialty: Mapped[Optional[str]] = mapped_column(String(300))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    modules: Mapped[List["CourseModule"]] = relationship(back_populates="lecturer")
    tracks: Mapped[List["CourseTrack"]] = relationship(back_populates="lecturer")
    exams: Mapped[List["Exam"]] = relationship(back_populates="lecturer")


# ============================================================
# CourseTrack (מסלול/מערך שיעורים) — מסלול ספציפי עם מרצה, יום, שעה ועיר
# ============================================================
class CourseTrack(Base):
    __tablename__ = "course_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)  # ראשון/שני/שלישי/רביעי/חמישי/שישי
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)  # HH:MM
    city: Mapped[str] = mapped_column(String(200), nullable=False)
    
    zoom_url: Mapped[Optional[str]] = mapped_column(String(500))
    price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    
    # Current progress tracking
    current_module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_modules.id"))
    current_session_number: Mapped[int] = mapped_column(Integer, default=1)
    last_session_date: Mapped[Optional[date]] = mapped_column(Date)
    next_entry_date: Mapped[Optional[date]] = mapped_column(Date)  # Computed: when next module starts
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_tracks_course", "course_id"),
        Index("idx_tracks_lecturer", "lecturer_id"),
        Index("idx_tracks_city", "city"),
        Index("idx_tracks_active", "is_active"),
    )

    # Relations
    course: Mapped["Course"] = relationship(back_populates="tracks")
    lecturer: Mapped["Lecturer"] = relationship(back_populates="tracks")
    current_module: Mapped[Optional["CourseModule"]] = relationship(foreign_keys=[current_module_id])
    sessions: Mapped[List["CourseSession"]] = relationship(back_populates="track", cascade="all, delete-orphan", order_by="CourseSession.session_date")
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="track")


# ============================================================
# CourseSession (שיעור מתוזמן) — שיעור ספציפי במסלול
# ============================================================
class CourseSession(Base):
    __tablename__ = "course_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("course_tracks.id", ondelete="CASCADE"), nullable=False)
    module_id: Mapped[int] = mapped_column(ForeignKey("course_modules.id"), nullable=False)
    
    session_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Session number within module (1-N)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    actual_start_time: Mapped[Optional[str]] = mapped_column(String(10))  # HH:MM
    actual_end_time: Mapped[Optional[str]] = mapped_column(String(10))  # HH:MM
    recording_url: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    status: Mapped[str] = mapped_column(String(50), default="מתוכנן")  # מתוכנן / התקיים / בוטל
    is_entry_point: Mapped[bool] = mapped_column(Boolean, default=False)  # True if session_number == 1
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_sessions_track", "track_id"),
        Index("idx_sessions_module", "module_id"),
        Index("idx_sessions_date", "session_date"),
        Index("idx_sessions_entry_point", "is_entry_point"),
    )

    # Relations
    track: Mapped["CourseTrack"] = relationship(back_populates="sessions")
    module: Mapped["CourseModule"] = relationship()
    attendance_records: Mapped[List["Attendance"]] = relationship(back_populates="session", cascade="all, delete-orphan")


# ============================================================
# Coupons (קופונים) — entity 15
# ============================================================
class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String(300))
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    discount_type: Mapped[Optional[str]] = mapped_column(String(50))  # אחוז / סכום קבוע
    discount_value: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    max_uses: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# Leads (לידים) — entity 1
# ============================================================
class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Basic details (Costumers_Details_grp_dup_e_79)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    family_name: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    phone2: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(200))
    id_number: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Source (g_309)
    source_type: Mapped[Optional[str]] = mapped_column(String(100))  # אינטרנט / ימות משיח / אחר
    source_name: Mapped[Optional[str]] = mapped_column(String(300))
    campaign_name: Mapped[Optional[str]] = mapped_column(String(300))
    source_message: Mapped[Optional[str]] = mapped_column(Text)
    source_details: Mapped[Optional[str]] = mapped_column(Text)
    arrival_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Salesperson (g_160_dup_e_79)
    salesperson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("salespeople.id"))

    # Conversion stages (g_349)
    status: Mapped[str] = mapped_column(String(100), default="ליד חדש")
    first_payment: Mapped[bool] = mapped_column(Boolean, default=False)
    first_lesson: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Lead response and follow-up tracking
    lead_response: Mapped[Optional[str]] = mapped_column(String(100))  # תגובת הליד: מעוניין / צריך לחשוב / לא זמין / לא מעוניין
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0)  # מספר ניסיונות מעקב
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # תאריך שיחה אחרונה
    
    # Discount tracking
    discount_notes: Mapped[Optional[str]] = mapped_column(Text)  # הערות על ההנחה שניתנה
    
    # Terms approval tracking
    approval_method: Mapped[Optional[str]] = mapped_column(String(50))  # שיטת אישור: טלפון / מייל / חתימה דיגיטלית / SMS
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # תאריך אישור תקנון

    # Links
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id", use_alter=True, name="fk_lead_student"))
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"))
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))  # Interested course
    requested_course: Mapped[Optional[str]] = mapped_column(String(300))  # Free text - what the lead asked for (from form)
    interested_track_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_tracks.id"))  # Interested track
    active_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_tasks.id", use_alter=True))
    
    # Selected course for sale (pricing comes from Course)
    selected_course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    selected_price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))  # Override price if needed
    selected_payments_count: Mapped[Optional[int]] = mapped_column(Integer)  # Override payments if needed
    selected_payment_day: Mapped[Optional[int]] = mapped_column(Integer)  # Day of month for payment
    
    # Payment tracking (before conversion)
    first_payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payments.id", use_alter=True))
    nedarim_payment_link: Mapped[Optional[str]] = mapped_column(String(500))  # Active payment link from Nedarim
    
    # ============================================================
    # Conversion Checklist - Lead to Student Journey
    # ============================================================
    
    # 1. Payment completion (סליקה)
    payment_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_completed_amount: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    payment_completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payment_completed_method: Mapped[Optional[str]] = mapped_column(String(50))  # אשראי/העברה/מזומן
    payment_reference: Mapped[Optional[str]] = mapped_column(String(200))  # אסמכתא
    payment_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # אושר ע"י נדרים פלוס
    
    # 2. Kinyan/Terms approval (קניון/תקנון)
    kinyan_signed: Mapped[bool] = mapped_column(Boolean, default=False)
    kinyan_signed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    kinyan_method: Mapped[Optional[str]] = mapped_column(String(50))  # PDF במייל / אישור טלפוני / IVR / חתימה דיגיטלית
    kinyan_file_url: Mapped[Optional[str]] = mapped_column(String(500))  # קישור לקובץ PDF אם קיים
    kinyan_notes: Mapped[Optional[str]] = mapped_column(Text)  # הערות על אישור התקנון
    
    # 3. Shipping details (פרטי משלוח)
    shipping_details_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    shipping_full_address: Mapped[Optional[str]] = mapped_column(Text)
    shipping_city: Mapped[Optional[str]] = mapped_column(String(200))
    shipping_postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    shipping_phone: Mapped[Optional[str]] = mapped_column(String(50))
    shipping_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # 4. Student chat integration (צ'אט תלמידים)
    student_chat_added: Mapped[bool] = mapped_column(Boolean, default=False)
    student_chat_link: Mapped[Optional[str]] = mapped_column(String(500))
    student_chat_platform: Mapped[Optional[str]] = mapped_column(String(50))  # WhatsApp/Telegram/Discord
    student_chat_added_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # 5. Handoff to class manager (העברה למנהל כיתות)
    handoff_to_manager: Mapped[bool] = mapped_column(Boolean, default=False)
    handoff_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    handoff_manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))  # מנהל הכיתות
    handoff_completed: Mapped[bool] = mapped_column(Boolean, default=False)  # מנהל אישר השלמה
    handoff_completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Overall conversion status (סטטוס המרה כללי)
    conversion_checklist_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    conversion_completed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # עריכה ידנית ע"י איש מכירות בלבד
    created_by: Mapped[Optional[str]] = mapped_column(String(200))

    __table_args__ = (
        Index("idx_leads_phone", "phone"),
        Index("idx_leads_status", "status"),
        Index("idx_leads_salesperson", "salesperson_id"),
        Index("idx_leads_campaign", "campaign_id"),
    )

    # Relations
    salesperson: Mapped[Optional["Salesperson"]] = relationship(back_populates="leads")
    campaign: Mapped[Optional["Campaign"]] = relationship(back_populates="leads")
    course: Mapped[Optional["Course"]] = relationship(foreign_keys=[course_id])  # Interested course
    interested_track: Mapped[Optional["CourseTrack"]] = relationship(foreign_keys=[interested_track_id])  # Interested track
    student: Mapped[Optional["Student"]] = relationship(foreign_keys=[student_id])  # Lead converted to this student
    interactions: Mapped[List["LeadInteraction"]] = relationship(back_populates="lead", order_by="LeadInteraction.interaction_date.desc()")
    products: Mapped[List["LeadProduct"]] = relationship(back_populates="lead", foreign_keys="LeadProduct.lead_id")
    selected_course: Mapped[Optional["Course"]] = relationship(foreign_keys=[selected_course_id])
    first_payment_rel: Mapped[Optional["Payment"]] = relationship(foreign_keys=[first_payment_id])
    payments: Mapped[List["Payment"]] = relationship(back_populates="lead", foreign_keys="Payment.lead_id")
    handoff_manager: Mapped[Optional["User"]] = relationship(foreign_keys=[handoff_manager_id])  # Class manager
    conversion_completed_by: Mapped[Optional["User"]] = relationship(foreign_keys=[conversion_completed_by_id])  # Who completed conversion


# ============================================================
# LeadInteraction (פניות/שיחות) — תקשורת + IVR + אתר
# ============================================================
class LeadInteraction(Base):
    __tablename__ = "lead_interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    # Type
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # 'ivr_call' / 'website_form' / 'outbound_call' / 'whatsapp' / 'email'
    interaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # IVR fields (ימות)
    call_status: Mapped[Optional[str]] = mapped_column(String(50))
    wait_time: Mapped[Optional[str]] = mapped_column(String(50))
    call_duration: Mapped[Optional[str]] = mapped_column(String(50))
    total_duration: Mapped[Optional[str]] = mapped_column(String(50))
    ivr_product: Mapped[Optional[str]] = mapped_column(String(200))

    # Website fields
    form_product: Mapped[Optional[str]] = mapped_column(String(200))
    form_content: Mapped[Optional[str]] = mapped_column(Text)

    # Communication fields (outbound)
    user_name: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    next_call_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_interactions_lead", "lead_id"),
        Index("idx_interactions_date", "interaction_date"),
    )

    lead: Mapped["Lead"] = relationship(back_populates="interactions")


# ============================================================
# LeadProduct (פרטי מוצר לליד) - replaces g_230
# ============================================================
class LeadProduct(Base):
    __tablename__ = "lead_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    payments_count: Mapped[Optional[int]] = mapped_column(Integer)
    monthly_payment: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    payment_day: Mapped[Optional[int]] = mapped_column(Integer)
    payment_type: Mapped[str] = mapped_column(String(50), default="הוראת קבע")
    language: Mapped[str] = mapped_column(String(20), default="עברית")

    coupon_id: Mapped[Optional[int]] = mapped_column(ForeignKey("coupons.id"))
    discount_type: Mapped[Optional[str]] = mapped_column(String(50))
    discount_amount: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    final_price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))

    # Course placement
    track_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_tracks.id"))
    entry_module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_modules.id"))
    entry_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_sessions.id"))
    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    sessions_remaining: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_finish: Mapped[Optional[date]] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["Lead"] = relationship(back_populates="products", foreign_keys=[lead_id])
    course: Mapped[Optional["Course"]] = relationship()
    coupon: Mapped[Optional["Coupon"]] = relationship()
    track: Mapped[Optional["CourseTrack"]] = relationship()
    entry_module: Mapped[Optional["CourseModule"]] = relationship()
    entry_session: Mapped[Optional["CourseSession"]] = relationship()


# ============================================================
# Students (תלמידים) — entity 2
# ============================================================
class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    id_number: Mapped[Optional[str]] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    phone2: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(100), default="תלמיד פעיל")
    approved_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Topics system - entry point tracking
    entry_point_lesson_id: Mapped[Optional[int]] = mapped_column(Integer)
    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    graduation_date: Mapped[Optional[date]] = mapped_column(Date)
    is_graduate: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Nedarim Plus integration
    nedarim_payer_id: Mapped[Optional[str]] = mapped_column(String(50))  # PAY_xxxxx

    # Link back to lead
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))

    # Payment summary
    total_price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    total_paid: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2), default=0)
    payment_status: Mapped[str] = mapped_column(String(50), default="חייב")
    shipping_status: Mapped[Optional[str]] = mapped_column(String(50))  # ממתין / נשלח / התקבל

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_students_phone", "phone"),
        Index("idx_students_status", "status"),
    )

    original_lead: Mapped[Optional["Lead"]] = relationship(foreign_keys=[lead_id])  # Student came from this lead
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="student")
    exam_submissions: Mapped[List["ExamSubmission"]] = relationship(back_populates="student")
    payments: Mapped[List["Payment"]] = relationship(back_populates="student")
    commitments: Mapped[List["Commitment"]] = relationship(back_populates="student")
    attendance_records: Mapped[List["Attendance"]] = relationship(back_populates="student")
    collections: Mapped[List["Collection"]] = relationship(back_populates="student")


# ============================================================
# Enrollments (הרשמות לקורסים)
# ============================================================
class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    track_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_tracks.id"))

    enrollment_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    entry_module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_modules.id"))
    entry_session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_sessions.id"))
    start_date: Mapped[Optional[date]] = mapped_column(Date)

    current_module: Mapped[int] = mapped_column(Integer, default=1)
    total_modules: Mapped[Optional[int]] = mapped_column(Integer)
    sessions_remaining: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_finish: Mapped[Optional[date]] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(50), default="פעיל")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_enrollments_student", "student_id"),
        Index("idx_enrollments_course", "course_id"),
        Index("idx_enrollments_track", "track_id"),
    )

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped[Optional["Course"]] = relationship(back_populates="enrollments")
    track: Mapped[Optional["CourseTrack"]] = relationship(back_populates="enrollments")
    entry_module: Mapped[Optional["CourseModule"]] = relationship()
    entry_session: Mapped[Optional["CourseSession"]] = relationship()


# ============================================================
# Payments (תשלומים) — entity 13
# ============================================================
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[Optional[str]] = mapped_column(String(200))  # אסמכתא נדרים פלוס
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"))
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    commitment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("commitments.id"))

    payment_date: Mapped[Optional[date]] = mapped_column(Date)
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default="₪")
    transaction_type: Mapped[Optional[str]] = mapped_column(String(50))  # רגיל / הוראת קבע / החזר
    installments: Mapped[Optional[int]] = mapped_column(Integer)
    charge_day: Mapped[Optional[int]] = mapped_column(Integer)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))  # אשראי / העברה / מזומן
    status: Mapped[str] = mapped_column(String(50), default="ממתין")  # שולם / ממתין / נכשל / הוחזר
    
    # Nedarim Plus integration
    nedarim_donation_id: Mapped[Optional[str]] = mapped_column(String(50))  # DON_xxxxx
    nedarim_transaction_id: Mapped[Optional[str]] = mapped_column(String(50))  # TRX_xxxxx

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_payments_student", "student_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_commitment", "commitment_id"),
        Index("idx_payments_nedarim", "nedarim_donation_id"),
    )

    lead: Mapped[Optional["Lead"]] = relationship(back_populates="payments", foreign_keys=[lead_id])
    student: Mapped[Optional["Student"]] = relationship(back_populates="payments")
    course: Mapped[Optional["Course"]] = relationship()
    commitment: Mapped[Optional["Commitment"]] = relationship(back_populates="payments")


# ============================================================
# Exams (מבחנים) — entity 11 (now general exam, submissions are children)
# ============================================================
class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecturers.id"))
    exam_date: Mapped[Optional[date]] = mapped_column(Date)
    exam_type: Mapped[str] = mapped_column(String(50), default="בכתב")  # בעל-פה / בכתב / מטלה
    questionnaire_url: Mapped[Optional[str]] = mapped_column(String(500))
    answers_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_exams_course", "course_id"),
    )

    course: Mapped["Course"] = relationship(back_populates="exams")
    lecturer: Mapped[Optional["Lecturer"]] = relationship(back_populates="exams")
    submissions: Mapped[List["ExamSubmission"]] = relationship(back_populates="exam", cascade="all, delete-orphan")


# ============================================================
# ExamSubmission (הגשות מבחנים) — child of Exam
# ============================================================
class ExamSubmission(Base):
    __tablename__ = "exam_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    score: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="הוגש")  # הוגש / נבדק / עבר / נכשל
    student_notes: Mapped[Optional[str]] = mapped_column(Text)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_exam_sub_exam", "exam_id"),
        Index("idx_exam_sub_student", "student_id"),
    )

    exam: Mapped["Exam"] = relationship(back_populates="submissions")
    student: Mapped["Student"] = relationship(back_populates="exam_submissions")


# ============================================================
# SalesTask (משימות מכירות) — entity 5
# ============================================================
class SalesTask(Base):
    __tablename__ = "sales_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    salesperson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("salespeople.id"))  # NULL if assigned to user
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"))

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="חדש")  # חדש / בטיפול / הושלם
    priority: Mapped[int] = mapped_column(Integer, default=0)  # 0-3
    
    # Extended fields for class manager tasks
    task_type: Mapped[str] = mapped_column(String(50), default="sales")  # sales / class_management / shipping / general
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))  # For class manager or other users
    auto_created: Mapped[bool] = mapped_column(Boolean, default=False)  # Auto-created by system
    parent_lead_conversion: Mapped[bool] = mapped_column(Boolean, default=False)  # Part of lead conversion process

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_tasks_salesperson", "salesperson_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_lead", "lead_id"),
        Index("idx_tasks_assigned_user", "assigned_to_user_id"),
        Index("idx_tasks_type", "task_type"),
    )

    salesperson: Mapped[Optional["Salesperson"]] = relationship(back_populates="tasks")
    assigned_to_user: Mapped[Optional["User"]] = relationship(foreign_keys=[assigned_to_user_id])
    reports: Mapped[List["TaskReport"]] = relationship(back_populates="task", cascade="all, delete-orphan")


# ============================================================
# TaskReport (דיווחי ביצוע) — child of SalesTask
# ============================================================
class TaskReport(Base):
    __tablename__ = "task_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("sales_tasks.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped["SalesTask"] = relationship(back_populates="reports")


# ============================================================
# EmailTemplate (תבניות מייל) — email templates with attachments
# ============================================================
class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))  # התרשמות / מעקב / כללי
    track_type: Mapped[Optional[str]] = mapped_column(String(100))  # מסלול התעניינות
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_email_templates_category", "category"),
        Index("idx_email_templates_active", "is_active"),
    )


# ============================================================
# LeadMessage (הודעות לידים) — entity 6
# ============================================================
class LeadMessage(Base):
    __tablename__ = "lead_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="טיוטה")  # טיוטה / נשלח / נכשל
    recipient_type: Mapped[Optional[str]] = mapped_column(String(50))  # lead / campaign / salesperson
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"))
    salesperson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("salespeople.id"))
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("email_templates.id"))  # תבנית ששימשה
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    send_method: Mapped[Optional[str]] = mapped_column(String(50))  # מייל / SMS / וואצאפ
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# ============================================================
# Inquiry (פניות נכנסות) — entity 7
# ============================================================
class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    inquiry_type: Mapped[str] = mapped_column(String(50), nullable=False)  # מייל / דואר קולי / טלפון / אחר
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="חדש")  # חדש / בטיפול / טופל / סגור
    notes: Mapped[Optional[str]] = mapped_column(Text)
    handled_by: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_inquiries_status", "status"),
        Index("idx_inquiries_lead", "lead_id"),
        Index("idx_inquiries_student", "student_id"),
    )

    responses: Mapped[List["InquiryResponse"]] = relationship(back_populates="inquiry", cascade="all, delete-orphan")


# ============================================================
# InquiryResponse (שרשור תגובות) — child of Inquiry
# ============================================================
class InquiryResponse(Base):
    __tablename__ = "inquiry_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id", ondelete="CASCADE"), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inquiry: Mapped["Inquiry"] = relationship(back_populates="responses")


# ============================================================
# Attendance (נוכחות ומטלות) — entity 12
# ============================================================
class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_sessions.id", ondelete="CASCADE"))
    module_id: Mapped[int] = mapped_column(ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False)
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecturers.id"))
    attendance_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assignment_done: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_attendance_student", "student_id"),
        Index("idx_attendance_session", "session_id"),
        Index("idx_attendance_module", "module_id"),
    )

    student: Mapped["Student"] = relationship(back_populates="attendance_records")
    session: Mapped[Optional["CourseSession"]] = relationship(back_populates="attendance_records")
    module: Mapped["CourseModule"] = relationship()
    lecturer: Mapped[Optional["Lecturer"]] = relationship()


# ============================================================
# Commitment (התחייבויות — הוראות קבע/סליקה) — entity 14
# ============================================================
class Commitment(Base):
    __tablename__ = "commitments"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[Optional[str]] = mapped_column(String(200))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    monthly_amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    installments: Mapped[Optional[int]] = mapped_column(Integer)
    charge_day: Mapped[Optional[int]] = mapped_column(Integer)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))  # אשראי / הוראת קבע
    status: Mapped[str] = mapped_column(String(50), default="פעיל")  # פעיל / מושהה / הסתיים / בוטל
    
    # Nedarim Plus integration
    nedarim_subscription_id: Mapped[Optional[str]] = mapped_column(String(50))  # SUB_xxxxx
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_commitments_student", "student_id"),
        Index("idx_commitments_status", "status"),
        Index("idx_commitments_nedarim", "nedarim_subscription_id"),
    )

    student: Mapped["Student"] = relationship(back_populates="commitments")
    course: Mapped[Optional["Course"]] = relationship()
    payments: Mapped[List["Payment"]] = relationship(back_populates="commitment")
    collections: Mapped[List["Collection"]] = relationship(back_populates="commitment")


# ============================================================
# Collection (גביה) — entity 16
# ============================================================
class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    commitment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("commitments.id"))
    payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payments.id"))  # Link to resulting payment
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    charge_day: Mapped[Optional[int]] = mapped_column(Integer)  # Day of month for recurring
    installment_number: Mapped[Optional[int]] = mapped_column(Integer)  # e.g., 3 of 12
    total_installments: Mapped[Optional[int]] = mapped_column(Integer)  # total planned installments
    
    status: Mapped[str] = mapped_column(String(50), default="ממתין")  # ממתין / נגבה / נכשל / בוטל
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reference: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Nedarim Plus integration
    nedarim_donation_id: Mapped[Optional[str]] = mapped_column(String(50))  # DON_xxxxx
    nedarim_transaction_id: Mapped[Optional[str]] = mapped_column(String(50))  # TRX_xxxxx
    nedarim_subscription_id: Mapped[Optional[str]] = mapped_column(String(50))  # From Commitment
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_collections_student", "student_id"),
        Index("idx_collections_status", "status"),
        Index("idx_collections_due_date", "due_date"),
        Index("idx_collections_nedarim", "nedarim_donation_id"),
        Index("idx_collections_commitment", "commitment_id"),
    )

    student: Mapped["Student"] = relationship(back_populates="collections")
    commitment: Mapped[Optional["Commitment"]] = relationship(back_populates="collections")
    payment: Mapped[Optional["Payment"]] = relationship()
    course: Mapped[Optional["Course"]] = relationship()


# ============================================================
# Expense (הוצאות) — entity 17
# ============================================================
class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)  # תיאור - חובה
    category: Mapped[Optional[str]] = mapped_column(String(100))  # קטגוריה
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    expense_date: Mapped[Optional[date]] = mapped_column(Date)  # תאריך הוצאה
    vendor: Mapped[Optional[str]] = mapped_column(String(300))  # ספק
    notes: Mapped[Optional[str]] = mapped_column(Text)  # הערות
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"))
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    invoice_file: Mapped[Optional[str]] = mapped_column(String(500))  # path/URL
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped[Optional["Course"]] = relationship()
    campaign: Mapped[Optional["Campaign"]] = relationship()


# ============================================================
# AuditLog (לוג פעולות במערכת) — system logging
# ============================================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))  # null for API/system actions
    user_name: Mapped[Optional[str]] = mapped_column(String(300))  # cached for display
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # create/update/delete/view/login/etc
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))  # leads/students/courses/etc
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)  # the ID of the affected record
    description: Mapped[Optional[str]] = mapped_column(Text)  # human-readable description
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    request_method: Mapped[Optional[str]] = mapped_column(String(10))  # GET/POST/PUT/DELETE
    request_path: Mapped[Optional[str]] = mapped_column(String(500))
    changes: Mapped[Optional[str]] = mapped_column(Text)  # JSON string of before/after values
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created", "created_at"),
    )

    user: Mapped[Optional["User"]] = relationship()


# ============================================================
# File (קבצים) — file storage tracking
# ============================================================
class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)  # original filename
    storage_key: Mapped[Optional[str]] = mapped_column(String(500), unique=True)  # R2 object key (nullable for DB storage)
    file_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary)  # Binary data if stored in DB
    content_type: Mapped[Optional[str]] = mapped_column(String(100))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Link to any entity (polymorphic)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))  # leads/students/expenses/messages/templates
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_files_entity", "entity_type", "entity_id"),
        Index("idx_files_storage_key", "storage_key"),
    )

    uploader: Mapped[Optional["User"]] = relationship()


# ============================================================
# WebhookLog (לוג וובהוקים) — audit trail for all incoming webhooks
# ============================================================
class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Webhook identification
    webhook_type: Mapped[str] = mapped_column(String(50), nullable=False)  # elementor/yemot/generic/nedarim/lesson-complete/kinyan-approval/file-upload
    source_ip: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Payload
    raw_payload: Mapped[Optional[str]] = mapped_column(Text)  # JSON string of raw incoming data
    parsed_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON string of parsed/normalized data
    
    # Processing result
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    action: Mapped[Optional[str]] = mapped_column(String(100))  # created/updated/processed/failed
    result_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON string of result
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Linked entity (what was created/updated)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50))  # lead/payment/session/file
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Timing
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_webhook_logs_type", "webhook_type"),
        Index("idx_webhook_logs_created", "created_at"),
        Index("idx_webhook_logs_entity", "entity_type", "entity_id"),
    )


# ============================================================
# WebhookQueue (תור וובהוקים כושלים) — queue for failed webhooks
# ============================================================
class WebhookQueue(Base):
    __tablename__ = "webhook_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    webhook_log_id: Mapped[int] = mapped_column(ForeignKey("webhook_logs.id", ondelete="CASCADE"), nullable=False)
    
    webhook_type: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    source_ip: Mapped[Optional[str]] = mapped_column(String(100))
    
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=5)
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_webhook_queue_status", "status"),
        Index("idx_webhook_queue_type", "webhook_type"),
        Index("idx_webhook_queue_created", "created_at"),
        Index("idx_webhook_queue_expires", "expires_at"),
        Index("idx_webhook_queue_next_retry", "next_retry_at"),
    )

    webhook_log: Mapped["WebhookLog"] = relationship()


# ============================================================
# Topic (נושא) — Topics/Semesters in a course
# ============================================================
class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    lessons_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("course_id", "order_index", name="uq_topic_course_order"),
        Index("idx_topics_course", "course_id"),
    )

    course: Mapped["Course"] = relationship()
    lessons: Mapped[List["Lesson"]] = relationship(back_populates="topic", cascade="all, delete-orphan", order_by="Lesson.lesson_number")


# ============================================================
# Lesson (מפגש) — Individual lesson/session in a topic
# ============================================================
class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_duration: Mapped[Optional[int]] = mapped_column(Integer)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    lecturer_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    assignment_title: Mapped[Optional[str]] = mapped_column(String(255))
    assignment_description: Mapped[Optional[str]] = mapped_column(Text)
    assignment_file_url: Mapped[Optional[str]] = mapped_column(String(500))
    assignment_due_days: Mapped[int] = mapped_column(Integer, default=7)
    
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("topic_id", "lesson_number", name="uq_lesson_topic_number"),
        Index("idx_lessons_topic", "topic_id"),
        Index("idx_lessons_course", "course_id"),
        Index("idx_lessons_scheduled", "scheduled_date"),
    )

    topic: Mapped["Topic"] = relationship(back_populates="lessons")
    course: Mapped["Course"] = relationship()
    progress_records: Mapped[List["StudentLessonProgress"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")


# ============================================================
# StudentLessonProgress (התקדמות תלמיד במפגש) — Track student progress per lesson
# ============================================================
class StudentLessonProgress(Base):
    __tablename__ = "student_lesson_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    
    attended: Mapped[bool] = mapped_column(Boolean, default=False)
    attendance_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    video_watched: Mapped[bool] = mapped_column(Boolean, default=False)
    video_watch_percentage: Mapped[int] = mapped_column(Integer, default=0)
    last_watched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    assignment_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    assignment_file_url: Mapped[Optional[str]] = mapped_column(String(500))
    assignment_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    assignment_grade: Mapped[Optional[int]] = mapped_column(Integer)
    assignment_feedback: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson"),
        Index("idx_progress_student", "student_id"),
        Index("idx_progress_lesson", "lesson_id"),
    )

    student: Mapped["Student"] = relationship()
    lesson: Mapped["Lesson"] = relationship(back_populates="progress_records")


# ============================================================
# InboundEmail (מיילים נכנסים/יוצאים) — synced via Make.com webhook
# ============================================================
class InboundEmail(Base):
    __tablename__ = "inbound_emails"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Gmail message identifiers
    gmail_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # Gmail message ID
    thread_id: Mapped[Optional[str]] = mapped_column(String(100))  # Gmail thread ID for threading

    # Direction: 'inbound' (INBOX) or 'outbound' (SENT)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="inbound")

    # Sender
    from_email: Mapped[str] = mapped_column(String(300), nullable=False)
    from_name: Mapped[Optional[str]] = mapped_column(String(300))

    # Recipients
    to_emails: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of {name, email}
    bcc_emails: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of {email}

    # Content
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    snippet: Mapped[Optional[str]] = mapped_column(String(500))
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)

    # Attachments
    has_attachment: Mapped[bool] = mapped_column(Boolean, default=False)
    attachments_count: Mapped[int] = mapped_column(Integer, default=0)

    # Gmail metadata
    label_ids: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of label IDs
    folder: Mapped[Optional[str]] = mapped_column(String(50))  # INBOX / SENT / IMPORTANT etc.
    message_id_header: Mapped[Optional[str]] = mapped_column(String(500))  # Message-ID header
    in_reply_to: Mapped[Optional[str]] = mapped_column(String(500))  # In-Reply-To header
    size_estimate: Mapped[Optional[int]] = mapped_column(Integer)
    history_id: Mapped[Optional[str]] = mapped_column(String(50))

    # Lead assignment
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"))
    matched_auto: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    email_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # internalDate from Gmail
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_inbound_gmail_id", "gmail_id", unique=True),
        Index("idx_inbound_thread", "thread_id"),
        Index("idx_inbound_from_email", "from_email"),
        Index("idx_inbound_lead", "lead_id"),
        Index("idx_inbound_direction", "direction"),
        Index("idx_inbound_date", "email_date"),
        Index("idx_inbound_folder", "folder"),
    )

    lead: Mapped[Optional["Lead"]] = relationship()


# ============================================================
# HistoryEntry (היסטוריית פעולות ליד) — track lead actions and events
# ============================================================
class HistoryEntry(Base):
    __tablename__ = "history_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "תשלום התקבל", "המרה לתלמיד"
    description: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)  # JSON object with additional details
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_history_lead", "lead_id"),
        Index("idx_history_action_type", "action_type"),
        Index("idx_history_created", "created_at"),
    )

    lead: Mapped["Lead"] = relationship()


# ============================================================
# ChatThread (שרשורי צ'אט) — DM / Group / Sales Team
# ============================================================
class ChatThread(Base):
    __tablename__ = "chat_threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_type: Mapped[str] = mapped_column(String(20), nullable=False, default="dm")  # dm / group
    title: Mapped[Optional[str]] = mapped_column(String(300))  # NULL for DM
    is_sales_team: Mapped[bool] = mapped_column(Boolean, default=False)  # special "all salespeople" thread
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_chat_threads_type", "thread_type"),
        Index("idx_chat_threads_sales_team", "is_sales_team"),
        Index("idx_chat_threads_updated", "updated_at"),
    )

    members: Mapped[List["ChatThreadMember"]] = relationship(back_populates="thread", cascade="all, delete-orphan")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="thread", cascade="all, delete-orphan")


# ============================================================
# ChatThreadMember (חברי שרשור צ'אט)
# ============================================================
class ChatThreadMember(Base):
    __tablename__ = "chat_thread_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_chat_thread_member"),
        Index("idx_chat_members_thread", "thread_id"),
        Index("idx_chat_members_user", "user_id"),
    )

    thread: Mapped["ChatThread"] = relationship(back_populates="members")


# ============================================================
# ChatMessage (הודעות צ'אט)
# ============================================================
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False)
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reply_to_message_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chat_messages.id", ondelete="SET NULL"))
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    pinned_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    pinned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_chat_msg_thread", "thread_id"),
        Index("idx_chat_msg_sender", "sender_user_id"),
        Index("idx_chat_msg_pinned", "is_pinned"),
        Index("idx_chat_msg_reply", "reply_to_message_id"),
        Index("idx_chat_msg_created", "created_at"),
    )

    thread: Mapped["ChatThread"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_user_id])
    reply_to: Mapped[Optional["ChatMessage"]] = relationship(remote_side="ChatMessage.id", foreign_keys=[reply_to_message_id])


# ============================================================
# PopupAnnouncement (הודעות פופ-אפ מתפרצות)
# ============================================================
class PopupAnnouncement(Base):
    __tablename__ = "popup_announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text)  # URL or base64 data URI
    cta_text: Mapped[Optional[str]] = mapped_column(String(100))  # call-to-action button text
    cta_link: Mapped[Optional[str]] = mapped_column(String(500))  # call-to-action URL

    # Styling
    theme: Mapped[str] = mapped_column(String(50), default="default")  # default/success/warning/fire/celebration
    animation: Mapped[str] = mapped_column(String(50), default="slideUp")  # slideUp/fadeIn/bounceIn/zoomIn

    # Targeting
    target_audience: Mapped[str] = mapped_column(String(50), default="all")  # all / salesperson / manager / admin
    min_permission_level: Mapped[int] = mapped_column(Integer, default=0)

    # Scheduling
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # NULL = immediately
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # NULL = no expiry
    show_count: Mapped[int] = mapped_column(Integer, default=1)  # how many times to show per user (0 = unlimited)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)  # saved as reusable template

    # Priority & ordering
    priority: Mapped[int] = mapped_column(Integer, default=0)  # higher = shown first

    # Metadata
    created_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_popup_active", "is_active"),
        Index("idx_popup_schedule", "start_at", "end_at"),
        Index("idx_popup_template", "is_template"),
    )

    dismissals: Mapped[List["PopupDismissal"]] = relationship(back_populates="announcement", cascade="all, delete-orphan")


# ============================================================
# PopupDismissal (סגירת פופ-אפ ע"י משתמש)
# ============================================================
class PopupDismissal(Base):
    __tablename__ = "popup_dismissals"

    id: Mapped[int] = mapped_column(primary_key=True)
    announcement_id: Mapped[int] = mapped_column(ForeignKey("popup_announcements.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seen_count: Mapped[int] = mapped_column(Integer, default=1)  # how many times user has seen it
    dismissed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("announcement_id", "user_id", name="uq_popup_dismissal"),
        Index("idx_popup_dismiss_user", "user_id"),
        Index("idx_popup_dismiss_ann", "announcement_id"),
    )

    announcement: Mapped["PopupAnnouncement"] = relationship(back_populates="dismissals")
