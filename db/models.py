"""
All SQLAlchemy models in one place.
Maps directly to PostgreSQL tables.
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
# Salespeople (אנשי מכירות) - replaces e_94
# ============================================================
class Salesperson(Base):
    __tablename__ = "salespeople"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    ref_code: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    leads: Mapped[List["Lead"]] = relationship(back_populates="salesperson")
    tasks: Mapped[List["SalesTask"]] = relationship(back_populates="salesperson")


# ============================================================
# Campaigns (קמפיינים) - replaces e_90
# ============================================================
class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    campaign_type: Mapped[Optional[str]] = mapped_column(String(100))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    leads: Mapped[List["Lead"]] = relationship(back_populates="campaign")


# ============================================================
# Products (מוצרים) - replaces e_73
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
# Courses (קורסים) - replaces e_80
# ============================================================
class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    semester: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    modules: Mapped[List["CourseModule"]] = relationship(back_populates="course", order_by="CourseModule.module_order")
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="course")


# ============================================================
# CourseModules (שיעורים/מודולים) - replaces e_83
# ============================================================
class CourseModule(Base):
    __tablename__ = "course_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    module_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_count: Mapped[Optional[int]] = mapped_column(Integer)
    hours_estimate: Mapped[Optional[Numeric]] = mapped_column(Numeric(5, 1))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("course_id", "module_order", name="uq_course_module_order"),
        Index("idx_modules_course", "course_id"),
    )

    course: Mapped["Course"] = relationship(back_populates="modules")


# ============================================================
# Coupons (קופונים) - replaces e_95
# ============================================================
class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    discount_type: Mapped[Optional[str]] = mapped_column(String(50))
    discount_value: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# Leads (לידים) - replaces e_79
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

    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[Optional[str]] = mapped_column(String(200))

    __table_args__ = (
        Index("idx_leads_phone", "phone"),
        Index("idx_leads_status", "status"),
        Index("idx_leads_salesperson", "salesperson_id"),
    )

    # Relations
    salesperson: Mapped[Optional["Salesperson"]] = relationship(back_populates="leads")
    campaign: Mapped[Optional["Campaign"]] = relationship(back_populates="leads")
    student: Mapped[Optional["Student"]] = relationship(back_populates="lead", foreign_keys=[student_id])
    interactions: Mapped[List["LeadInteraction"]] = relationship(back_populates="lead", order_by="LeadInteraction.interaction_date.desc()")
    products: Mapped[List["LeadProduct"]] = relationship(back_populates="lead")


# ============================================================
# LeadInteraction (פניות/שיחות) - replaces g_286 + g_286_dup_123 + g_183
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
# Students (תלמידים) - replaces clients
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
    nedarim_id: Mapped[Optional[str]] = mapped_column(String(50))

    # Link back to lead
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))

    # Payment summary
    total_price: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2))
    total_paid: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2), default=0)
    payment_status: Mapped[str] = mapped_column(String(50), default="חייב")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_students_phone", "phone"),
        Index("idx_students_status", "status"),
    )

    lead: Mapped[Optional["Lead"]] = relationship(back_populates="student", foreign_keys=[lead_id])
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="student")
    exams: Mapped[List["Exam"]] = relationship(back_populates="student")
    payments: Mapped[List["Payment"]] = relationship(back_populates="student")


# ============================================================
# Enrollments (הרשמות לקורסים) - replaces g_191
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
# Payments (תשלומים) - replaces e_88
# ============================================================
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"))
    lead_id: Mapped[Optional[int]] = mapped_column(ForeignKey("leads.id"))

    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="ממתין")
    reference: Mapped[Optional[str]] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_payments_student", "student_id"),
    )

    student: Mapped[Optional["Student"]] = relationship(back_populates="payments")


# ============================================================
# Exams (מבחנים וציונים) - replaces e_85/e_86/g_313
# ============================================================
class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    exam_name: Mapped[str] = mapped_column(String(300), nullable=False)
    course_id: Mapped[Optional[int]] = mapped_column(ForeignKey("courses.id"))
    score: Mapped[Optional[Numeric]] = mapped_column(Numeric(5, 2))
    exam_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_exams_student", "student_id"),
    )

    student: Mapped["Student"] = relationship(back_populates="exams")
    course: Mapped[Optional["Course"]] = relationship()


# ============================================================
# SalesTask (משימות לאנשי מכירות) - replaces e_108
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
    status: Mapped[str] = mapped_column(String(50), default="פתוח")
    priority: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_tasks_salesperson", "salesperson_id"),
        Index("idx_tasks_status", "status"),
    )

    salesperson: Mapped["Salesperson"] = relationship(back_populates="tasks")
