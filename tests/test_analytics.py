from pathlib import Path

import polars as pl

from insightforge.analytics.workbooks import apply_transform, profile_dataframe, read_workbook


def test_profile_reports_quality_signals():
    frame = pl.DataFrame(
        {
            "region": ["East", "West", "East", "East"],
            "revenue": [100.0, 200.0, None, 100.0],
            "units": [2, 4, 3, 2],
        }
    )
    profile = profile_dataframe(frame)
    assert profile["rows"] == 4
    assert profile["columns"] == 3
    assert profile["null_cells"] == 1
    assert profile["duplicate_rows"] == 1
    assert 0 < profile["quality_score"] < 100
    revenue = next(item for item in profile["column_profiles"] if item["name"] == "revenue")
    assert revenue["mean"] == 133.33333333333334


def test_filter_sort_group_transformations():
    frame = pl.DataFrame({"region": ["East", "West", "East"], "revenue": [100, 200, 50]})
    filtered = apply_transform(
        frame, {"operation": "filter", "column": "region", "operator": "eq", "value": "East"}
    )
    assert filtered.height == 2
    sorted_frame = apply_transform(
        frame, {"operation": "sort", "column": "revenue", "descending": True}
    )
    assert sorted_frame["revenue"].to_list() == [200, 100, 50]
    grouped = apply_transform(
        frame,
        {"operation": "group", "column": "region", "measure": "revenue", "aggregation": "sum"},
    )
    assert grouped.columns == ["region", "sum"]
    assert grouped["sum"].to_list() == [200, 150]


def test_excel_reader_supports_workbook_sheet(tmp_path: Path):
    destination = tmp_path / "sample.xlsx"
    frame = pl.DataFrame({"month": ["Jan", "Feb"], "sales": [10, 20]})
    frame.write_excel(destination, worksheet="Sales")
    loaded = read_workbook(destination, "Sales")
    assert loaded.columns == ["month", "sales"]
    assert loaded.height == 2
