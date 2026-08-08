"""User dashboard and saved visualization routes."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter
from sqlalchemy import desc, select

from insightforge.api.dependencies import CurrentUser, DbSession
from insightforge.api.schemas import DashboardOut, DashboardUpdate, DashboardWidget
from insightforge.core.models import Dashboard, Dataset

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _default_widgets(dataset: Dataset | None) -> list[DashboardWidget]:
    if dataset is None:
        return [
            DashboardWidget(
                id="welcome",
                kind="activity",
                title="Your first insight is waiting",
                subtitle="Upload an Excel workbook to light up the workspace.",
                color="#7C5CFC",
                position=0,
            ),
            DashboardWidget(
                id="workflow",
                kind="insight",
                title="A calmer way to analyze",
                subtitle="Profile, explore, visualize, and export from one focused workspace.",
                color="#23C4A0",
                position=1,
            ),
        ]
    return [
        DashboardWidget(
            id="quality",
            kind="kpi",
            title="Dataset health",
            value=f"{dataset.quality_score:.0f}%",
            subtitle=f"{dataset.filename} quality score",
            color="#23C4A0",
            position=0,
        ),
        DashboardWidget(
            id="rows",
            kind="kpi",
            title="Rows explored",
            value=f"{dataset.row_count:,}",
            subtitle=f"Across {dataset.column_count} columns",
            color="#7C5CFC",
            position=1,
        ),
        DashboardWidget(
            id="insight",
            kind="insight",
            title="Next best move",
            subtitle="Open the analysis studio to find trends, gaps, and outliers.",
            color="#F29E4C",
            position=2,
        ),
        DashboardWidget(
            id="activity",
            kind="activity",
            title="Latest workbook",
            subtitle=f"{dataset.filename} is ready to explore.",
            color="#5E8BFF",
            position=3,
        ),
    ]


def _to_out(item: Dashboard) -> DashboardOut:
    return DashboardOut(
        id=item.id,
        name=item.name,
        widgets=[
            DashboardWidget.model_validate(value) for value in json.loads(item.layout_json or "[]")
        ],
        updated_at=item.updated_at,
    )


@router.get("", response_model=DashboardOut)
def get_dashboard(user: CurrentUser, db: DbSession) -> DashboardOut:
    item = db.scalar(
        select(Dashboard).where(Dashboard.user_id == user.id).order_by(Dashboard.created_at)
    )
    if item is None:
        latest = db.scalar(
            select(Dataset).where(Dataset.user_id == user.id).order_by(desc(Dataset.created_at))
        )
        widgets = _default_widgets(latest)
        item = Dashboard(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="My command center",
            layout_json=json.dumps([widget.model_dump() for widget in widgets]),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
    return _to_out(item)


@router.put("", response_model=DashboardOut)
def update_dashboard(payload: DashboardUpdate, user: CurrentUser, db: DbSession) -> DashboardOut:
    item = db.scalar(
        select(Dashboard).where(Dashboard.user_id == user.id).order_by(Dashboard.created_at)
    )
    if item is None:
        item = Dashboard(id=str(uuid.uuid4()), user_id=user.id, name=payload.name, layout_json="[]")
        db.add(item)
    item.name = payload.name
    item.layout_json = json.dumps([widget.model_dump() for widget in payload.widgets])
    db.commit()
    db.refresh(item)
    return _to_out(item)
