"""
Shared schema definitions - Single source of truth for API contracts.
These Pydantic models are used for:
1. FastAPI request/response validation
2. OpenAPI schema generation (→ TypeScript types)
3. Documentation

All API endpoints should use these schemas, not inline classes.
Frontend types are auto-generated from these via: python scripts/generate_types.py
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================
# Lead Schemas
# ============================================================
class LeadBase(BaseModel):
    """Base lead fields (shared between create/update/response)"""
    full_name: str = Field(default="", description="שם פרטי")
    family_name: Optional[str] = Field(default=None, description="שם משפחה")
    phone: str = Field(..., description="טלפון ראשי")
    phone2: Optional[str] = Field(default=None, description="טלפון נוסף")
    email: Optional[str] = Field(default=None, description="אימייל")
    address: Optional[str] = Field(default=None, description="כתובת")
    city: Optional[str] = Field(default=None, description="עיר")
    id_number: Optional[str] = Field(default=None, description="תעודת זהות")
    notes: Optional[str] = Field(default=None, description="הערות")
    source_type: Optional[str] = Field(default=None, description="סוג מקור (אינטרנט/ימות/אחר)")
    source_name: Optional[str] = Field(default=None, description="שם המקור")
    campaign_name: Optional[str] = Field(default=None, description="שם הקמפיין (טקסט)")
    source_message: Optional[str] = Field(default=None, description="הודעת המקור")
    source_details: Optional[str] = Field(default=None, description="פרטים נוספים")
    salesperson_id: Optional[int] = Field(default=None, description="מזהה איש מכירות")
    campaign_id: Optional[int] = Field(default=None, description="מזהה קמפיין")
    course_id: Optional[int] = Field(default=None, description="מזהה קורס מבוקש")


class LeadCreate(LeadBase):
    """Schema for creating a new lead"""
    pass


class LeadUpdate(BaseModel):
    """Schema for updating an existing lead (all fields optional)"""
    full_name: Optional[str] = None
    family_name: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    id_number: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    source_message: Optional[str] = None
    source_details: Optional[str] = None
    salesperson_id: Optional[int] = None
    campaign_id: Optional[int] = None
    course_id: Optional[int] = None


class LeadInteractionResponse(BaseModel):
    """Lead interaction response schema"""
    id: int
    type: str
    description: Optional[str] = None
    call_status: Optional[str] = None
    user_name: Optional[str] = None
    created_at: str

class LeadResponse(LeadBase):
    """Full lead response with all fields"""
    id: int
    status: str = "ליד חדש"
    created_at: str
    updated_at: Optional[str] = None
    interactions: List[LeadInteractionResponse] = []

    class Config:
        from_attributes = True


class LeadListItem(BaseModel):
    """Minimal lead for list views"""
    id: int
    full_name: str
    phone: str
    status: str
    salesperson_id: Optional[int] = None
    created_at: str


# ============================================================
# Student Schemas
# ============================================================
class StudentBase(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = None
    id_number: Optional[str] = None
    notes: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    status: str
    payment_status: str
    total_price: Optional[float] = None
    total_paid: Optional[float] = None
    created_at: str

    class Config:
        from_attributes = True


# ============================================================
# Salesperson Schemas
# ============================================================
class SalespersonResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


# ============================================================
# Common Response Schemas
# ============================================================
class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    has_more: bool
