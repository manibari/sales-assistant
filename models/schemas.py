"""Pydantic models for SPMS data validation."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnnualPlan(BaseModel):
    product_id: str
    product_name: str
    quota_fy26: float = 0
    strategy: Optional[str] = None
    target_industry: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DecisionMaker(BaseModel):
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    notes: str = ""


class Champion(BaseModel):
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    notes: str = ""


class CRM(BaseModel):
    client_id: str
    company_name: str
    industry: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    decision_maker: Optional[DecisionMaker] = None
    champions: Optional[list[Champion]] = None
    contact_info: Optional[str] = None
    notes: Optional[str] = None
    data_year: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Project(BaseModel):
    project_id: Optional[int] = None  # SERIAL, auto-generated
    project_name: str
    client_id: Optional[str] = None
    product_id: Optional[str] = None
    status_code: str = "L0"
    status_updated_at: Optional[datetime] = None
    presale_owner: Optional[str] = None
    postsale_owner: Optional[str] = None
    priority: str = "Medium"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SalesPlan(BaseModel):
    plan_id: Optional[int] = None  # SERIAL, auto-generated
    project_id: int
    product_id: Optional[str] = None
    expected_invoice_date: Optional[date] = None
    amount: float = 0
    confidence_level: float = Field(default=0.5, ge=0, le=1)
    prime_contractor: bool = True
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkLog(BaseModel):
    log_id: Optional[int] = None  # SERIAL, auto-generated
    project_id: int
    log_date: date = Field(default_factory=date.today)
    action_type: str
    content: Optional[str] = None
    duration_hours: float = 1.0
    source: str = "manual"
    ref_id: Optional[int] = None
    created_at: Optional[datetime] = None


class AppSetting(BaseModel):
    key: str
    value: str
