"""
All SQLAlchemy models in one place.
Maps directly to PostgreSQL tables.
Full spec: ENTITIES_SPEC.md (17 entities + child tables)
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, Numeric, Boolean, Date, DateTime,
    ForeignKey, Index, UniqueConstraint, ARRAY, func
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

    # Permission level: 0=pending, 10=viewer, 20=editor, 30=manager, 40=admin
    permission_level: Mapped[int] = mapped_column(Integer, default=0)
    role_name: Mapped[str] = mapped_column(String(50), default="pending")  # pending/viewer/editor/manager/admin

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
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    ref_code: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    leads: Mapped[List["Lead"]] = relationship(back_populates="salesperson")
    tasks: Mapped[List["SalesTask"]] = relationship(back_populates="salesperson")
    campaign_links: Mapped[List["CampaignSalespersonLink"]] = relationship(back_populates="salesperson")


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
# Products (מוצרים)
# ============================================================
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    product_number: Mapped[Optional[str]] = mapped_column(String(50))
    product_number_en: Mapped[Optional[str]] = mapped_column(String(50))
    price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    payments_count: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    modules: Mapped[List["CourseModule"]] = relationship(back_populates="course", order_by="CourseModule.module_order")
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
    exams: Mapped[List["Exam"]] = relationship(back_populates="lecturer")


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

    # Links
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"))
    campaign_id: Mapped[Optional[int]] = mapped_column(ForeignKey("campaigns.id"))
    active_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales_tasks.id", use_alter=True))

    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
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
    student: Mapped[Optional["Student"]] = relationship(foreign_keys=[student_id])  # Lead converted to this student
    interactions: Mapped[List["LeadInteraction"]] = relationship(back_populates="lead", order_by="LeadInteraction.interaction_date.desc()")
    products: Mapped[List["LeadProduct"]] = relationship(back_populates="lead")


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

    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
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
    entry_module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_modules.id"))
    entry_date: Mapped[Optional[date]] = mapped_column(Date)
    sessions_remaining: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_finish: Mapped[Optional[date]] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["Lead"] = relationship(back_populates="products")
    product: Mapped[Optional["Product"]] = relationship()
    coupon: Mapped[Optional["Coupon"]] = relationship()
    entry_module: Mapped[Optional["CourseModule"]] = relationship()


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

    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))

    enrollment_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    entry_module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_modules.id"))
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
    )

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped[Optional["Course"]] = relationship(back_populates="enrollments")
    product: Mapped[Optional["Product"]] = relationship()
    entry_module: Mapped[Optional["CourseModule"]] = relationship()


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
    salesperson_id: Mapped[int] = mapped_column(ForeignKey("salespeople.id"), nullable=False)
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"))

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="חדש")  # חדש / בטיפול / הושלם
    priority: Mapped[int] = mapped_column(Integer, default=0)  # 0-3

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_tasks_salesperson", "salesperson_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_lead", "lead_id"),
    )

    salesperson: Mapped["Salesperson"] = relationship(back_populates="tasks")
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
    module_id: Mapped[int] = mapped_column(ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False)
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lecturers.id"))
    attendance_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assignment_done: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_attendance_student", "student_id"),
        Index("idx_attendance_module", "module_id"),
    )

    student: Mapped["Student"] = relationship(back_populates="attendance_records")
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


# ============================================================
# Collection (גביה) — entity 16
# ============================================================
class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    commitment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("commitments.id"))
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ממתין")  # ממתין / נגבה / נכשל / בוטל
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reference: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_collections_student", "student_id"),
        Index("idx_collections_status", "status"),
        Index("idx_collections_due_date", "due_date"),
    )

    student: Mapped["Student"] = relationship(back_populates="collections")
    commitment: Mapped[Optional["Commitment"]] = relationship()


# ============================================================
# Expense (הוצאות) — entity 17
# ============================================================
class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor: Mapped[str] = mapped_column(String(300), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
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
