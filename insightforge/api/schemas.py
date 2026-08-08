"""Typed HTTP contracts for the InsightForge API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from insightforge.core.security import password_requirements


def _validate_password(value: str) -> str:
    missing = password_requirements(value)
    if missing:
        raise ValueError(f"Password must include {', '.join(missing)}.")
    return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    plan: str
    created_at: datetime | None = None


class SignupRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Name is required")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password(value)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class MessageResponse(BaseModel):
    message: str
    development_token: str | None = None


class DatasetOut(BaseModel):
    id: str
    filename: str
    sheet_name: str
    row_count: int
    column_count: int
    file_size: int
    quality_score: float
    status: str
    columns: list[dict[str, Any]]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DatasetProfileOut(BaseModel):
    dataset: DatasetOut
    profile: dict[str, Any]
    preview: list[dict[str, Any]]
    sheets: list[str] = []


class TransformRequest(BaseModel):
    operation: Literal["filter", "sort", "group", "rename", "drop_nulls"]
    column: str | None = None
    value: Any | None = None
    operator: str | None = None
    descending: bool = False
    measure: str | None = None
    aggregation: Literal["sum", "mean", "min", "max", "count"] = "sum"
    new_name: str | None = None


class ChartRequest(BaseModel):
    name: str = Field(default="Untitled insight", min_length=1, max_length=120)
    chart_type: Literal["bar", "line", "scatter", "histogram", "pie"] = "bar"
    x_column: str | None = None
    y_column: str | None = None
    color_column: str | None = None
    aggregation: Literal["sum", "mean", "min", "max", "count"] = "sum"


class VisualizationOut(BaseModel):
    id: str
    name: str
    chart_type: str
    dataset_id: str | None
    spec: dict[str, Any]
    created_at: datetime | None = None


class DashboardWidget(BaseModel):
    id: str
    kind: Literal["kpi", "insight", "chart", "activity"]
    title: str
    value: str | None = None
    subtitle: str | None = None
    color: str | None = None
    visualization_id: str | None = None
    position: int = 0
    hidden: bool = False


class DashboardOut(BaseModel):
    id: str
    name: str
    widgets: list[DashboardWidget]
    updated_at: datetime | None = None


class DashboardUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    widgets: list[DashboardWidget]
