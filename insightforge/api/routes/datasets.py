"""Dataset upload, profiling, transformations, charts, and export routes."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, select

from insightforge.analytics.workbooks import (
    apply_transform,
    column_summary,
    data_for_chart,
    discover_sheets,
    export_dataframe,
    jsonable,
    profile_dataframe,
    read_workbook,
    records,
)
from insightforge.api.dependencies import CurrentUser, DbSession
from insightforge.api.schemas import (
    ChartRequest,
    DatasetOut,
    DatasetProfileOut,
    TransformRequest,
    VisualizationOut,
)
from insightforge.core.config import settings
from insightforge.core.models import Dataset, User, Visualization

router = APIRouter(prefix="/datasets", tags=["datasets"])
ALLOWED_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _dataset_out(dataset: Dataset) -> DatasetOut:
    return DatasetOut(
        id=dataset.id,
        filename=dataset.filename,
        sheet_name=dataset.sheet_name,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        file_size=dataset.file_size,
        quality_score=dataset.quality_score,
        status=dataset.status,
        columns=json.loads(dataset.columns_json or "[]"),
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


def _owned_dataset(dataset_id: str, user: User, db: DbSession) -> Dataset:
    dataset = db.scalar(select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user.id))
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(user: CurrentUser, db: DbSession) -> list[DatasetOut]:
    datasets = db.scalars(
        select(Dataset).where(Dataset.user_id == user.id).order_by(desc(Dataset.created_at))
    ).all()
    return [_dataset_out(item) for item in datasets]


@router.post("/upload", response_model=DatasetProfileOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
) -> DatasetProfileOut:
    filename = file.filename or "workbook.xlsx"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, detail="Upload an Excel workbook (.xlsx, .xlsm, or .xls)"
        )
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Workbook is larger than the 50 MB limit")
    dataset_id = str(uuid.uuid4())
    destination = settings.upload_dir / f"{dataset_id}{suffix}"
    destination.write_bytes(data)
    try:
        sheets = discover_sheets(destination)
        selected_sheet = sheet_name if sheet_name in sheets else sheets[0]
        frame = read_workbook(destination, selected_sheet)
        profile = profile_dataframe(frame)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    dataset = Dataset(
        id=dataset_id,
        user_id=user.id,
        filename=filename,
        storage_path=str(destination),
        sheet_name=selected_sheet,
        row_count=frame.height,
        column_count=frame.width,
        file_size=len(data),
        quality_score=profile["quality_score"],
        columns_json=json.dumps(column_summary(frame)),
        profile_json=json.dumps(jsonable(profile)),
        preview_json=json.dumps(jsonable(profile["preview"])),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return DatasetProfileOut(
        dataset=_dataset_out(dataset), profile=profile, preview=profile["preview"], sheets=sheets
    )


@router.get("/{dataset_id}", response_model=DatasetProfileOut)
def get_dataset(dataset_id: str, user: CurrentUser, db: DbSession) -> DatasetProfileOut:
    dataset = _owned_dataset(dataset_id, user, db)
    profile = json.loads(dataset.profile_json or "{}")
    sheets = discover_sheets(Path(dataset.storage_path))
    return DatasetProfileOut(
        dataset=_dataset_out(dataset),
        profile=profile,
        preview=json.loads(dataset.preview_json or "[]"),
        sheets=sheets,
    )


@router.post("/{dataset_id}/transform")
def transform_dataset(
    dataset_id: str, payload: TransformRequest, user: CurrentUser, db: DbSession
) -> dict:
    dataset = _owned_dataset(dataset_id, user, db)
    try:
        frame = read_workbook(Path(dataset.storage_path), dataset.sheet_name)
        transformed = apply_transform(frame, payload.model_dump(exclude_none=True))
        profile = profile_dataframe(transformed)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "rows": transformed.height,
        "columns": column_summary(transformed),
        "profile": profile,
        "preview": records(transformed),
    }


@router.post("/{dataset_id}/chart", response_model=VisualizationOut)
def create_chart(
    dataset_id: str, payload: ChartRequest, user: CurrentUser, db: DbSession
) -> VisualizationOut:
    dataset = _owned_dataset(dataset_id, user, db)
    try:
        frame = read_workbook(Path(dataset.storage_path), dataset.sheet_name)
        spec = payload.model_dump()
        chart = data_for_chart(frame, spec)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    visualization = Visualization(
        id=str(uuid.uuid4()),
        user_id=user.id,
        dataset_id=dataset.id,
        name=payload.name,
        chart_type=payload.chart_type,
        spec_json=json.dumps({"config": spec, "chart": jsonable(chart)}),
    )
    db.add(visualization)
    db.commit()
    db.refresh(visualization)
    return VisualizationOut(
        id=visualization.id,
        name=visualization.name,
        chart_type=visualization.chart_type,
        dataset_id=visualization.dataset_id,
        spec=json.loads(visualization.spec_json),
        created_at=visualization.created_at,
    )


@router.get("/{dataset_id}/export")
def export_dataset(
    dataset_id: str, user: CurrentUser, db: DbSession, format: str = "xlsx"
) -> FileResponse:
    dataset = _owned_dataset(dataset_id, user, db)
    if format not in {"xlsx", "csv"}:
        raise HTTPException(status_code=400, detail="Export format must be xlsx or csv")
    try:
        frame = read_workbook(Path(dataset.storage_path), dataset.sheet_name)
        destination = settings.export_dir / f"{dataset.id}-{Path(dataset.filename).stem}.{format}"
        export_dataframe(frame, destination, format)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return FileResponse(
        destination, filename=destination.name, media_type="application/octet-stream"
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: str, user: CurrentUser, db: DbSession) -> None:
    dataset = _owned_dataset(dataset_id, user, db)
    Path(dataset.storage_path).unlink(missing_ok=True)
    db.delete(dataset)
    db.commit()


@router.get("/visualizations/mine", response_model=list[VisualizationOut])
def list_visualizations(user: CurrentUser, db: DbSession) -> list[VisualizationOut]:
    items = db.scalars(
        select(Visualization)
        .where(Visualization.user_id == user.id)
        .order_by(desc(Visualization.created_at))
    ).all()
    return [
        VisualizationOut(
            id=item.id,
            name=item.name,
            chart_type=item.chart_type,
            dataset_id=item.dataset_id,
            spec=json.loads(item.spec_json or "{}"),
            created_at=item.created_at,
        )
        for item in items
    ]
