from __future__ import annotations

import io
import uuid

from fastapi.testclient import TestClient
from openpyxl import Workbook

from insightforge.api.server import app


def _workbook_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales"
    sheet.append(["region", "revenue", "units"])
    sheet.append(["East", 100, 2])
    sheet.append(["West", 200, 4])
    sheet.append(["East", 75, 1])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_signup_rejects_a_password_that_fails_complexity_policy():
    client = TestClient(app)
    response = client.post(
        "/api/auth/signup",
        json={
            "email": f"weak-{uuid.uuid4().hex[:10]}@example.com",
            "full_name": "Test Explorer",
            "password": "alllowercasepassword",
        },
    )

    assert response.status_code == 422
    assert "Password must include" in response.text


def test_auth_dataset_chart_and_dashboard_flow():
    client = TestClient(app)
    email = f"tester-{uuid.uuid4().hex[:10]}@example.com"
    signup = client.post(
        "/api/auth/signup",
        json={
            "email": email,
            "full_name": "Test Explorer",
            "password": "CorrectHorse!42",
        },
    )
    assert signup.status_code == 201, signup.text
    access_token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    uploaded = client.post(
        "/api/datasets/upload",
        headers=headers,
        files={
            "file": (
                "sales.xlsx",
                _workbook_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert uploaded.status_code == 201, uploaded.text
    dataset = uploaded.json()["dataset"]
    assert dataset["row_count"] == 3
    assert dataset["quality_score"] == 100.0

    listed = client.get("/api/datasets", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == dataset["id"]

    transformed = client.post(
        f"/api/datasets/{dataset['id']}/transform",
        headers=headers,
        json={"operation": "filter", "column": "region", "operator": "eq", "value": "East"},
    )
    assert transformed.status_code == 200, transformed.text
    assert transformed.json()["rows"] == 2

    chart = client.post(
        f"/api/datasets/{dataset['id']}/chart",
        headers=headers,
        json={
            "name": "Revenue by region",
            "chart_type": "bar",
            "x_column": "region",
            "y_column": "revenue",
            "aggregation": "sum",
        },
    )
    assert chart.status_code == 200, chart.text
    assert chart.json()["spec"]["chart"]["chart_type"] == "bar"

    dashboard = client.get("/api/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["widgets"]

    reset = client.post("/api/auth/password-reset/request", json={"email": email})
    assert reset.status_code == 200
    token = reset.json()["development_token"]
    confirmed = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "password": "NewCorrectHorse!42"},
    )
    assert confirmed.status_code == 200
    logged_in = client.post(
        "/api/auth/login", json={"email": email, "password": "NewCorrectHorse!42"}
    )
    assert logged_in.status_code == 200
