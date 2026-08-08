"""Reusable presentation components for the Flet client."""

from __future__ import annotations

from typing import Any

import flet as ft
import flet_charts as fch

from insightforge.ui.theme import (
    BG,
    BLUE,
    INK,
    LINE,
    MINT,
    MINT_LIGHT,
    MUTED,
    ORANGE,
    ORANGE_LIGHT,
    PURPLE,
    PURPLE_LIGHT,
    RED,
    icon_box,
    label,
    surface,
)


def brand_mark(light: bool = False, compact: bool = False) -> ft.Row:
    foreground = ft.Colors.WHITE if light else INK
    accent = "#A995FF" if light else PURPLE
    if compact:
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=20),
                    width=38,
                    height=38,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=accent,
                    border_radius=12,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    return ft.Row(
        controls=[
            ft.Container(
                content=ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=20),
                width=38,
                height=38,
                alignment=ft.Alignment.CENTER,
                bgcolor=accent,
                border_radius=12,
            ),
            ft.Column(
                controls=[
                    ft.Text("InsightForge", size=18, weight=ft.FontWeight.W_700, color=foreground),
                    ft.Text(
                        "DATA / CLARITY",
                        size=9,
                        weight=ft.FontWeight.W_600,
                        color="#9BA8BE" if light else MUTED,
                    ),
                ],
                spacing=1,
            ),
        ],
        spacing=10,
    )


def stat_card(
    icon, heading: str, value: str, detail: str, accent: str = PURPLE, tint: str = PURPLE_LIGHT
) -> ft.Container:
    return surface(
        ft.Column(
            controls=[
                ft.Row(
                    [
                        icon_box(icon, accent, tint),
                        ft.Container(expand=True),
                        label("LIVE", 10, accent, ft.FontWeight.W_700),
                    ]
                ),
                ft.Container(height=14),
                label(heading.upper(), 11, MUTED, ft.FontWeight.W_600),
                ft.Text(value, size=28, color=INK, weight=ft.FontWeight.W_700),
                label(detail, 12, MUTED),
            ],
            spacing=4,
        ),
        padding=18,
    )


def insight_card(widget: dict[str, Any]) -> ft.Container:
    color = widget.get("color") or PURPLE
    kind = widget.get("kind", "insight")
    icon = ft.Icons.INSIGHTS if kind == "insight" else ft.Icons.AUTO_AWESOME
    tint = PURPLE_LIGHT if color == PURPLE else MINT_LIGHT if color == MINT else ORANGE_LIGHT
    return surface(
        ft.Column(
            controls=[
                ft.Row(
                    [
                        icon_box(icon, color, tint),
                        ft.Container(expand=True),
                        ft.Icon(ft.Icons.MORE_HORIZ, color=MUTED),
                    ]
                ),
                ft.Container(height=14),
                ft.Text(
                    widget.get("title", "Insight"), size=16, color=INK, weight=ft.FontWeight.W_700
                ),
                label(widget.get("subtitle", ""), 12, MUTED),
            ],
            spacing=5,
        ),
        padding=18,
    )


def empty_state(
    title_text: str, description: str, button: ft.Control | None = None
) -> ft.Container:
    controls: list[ft.Control] = [
        icon_box(ft.Icons.AUTO_AWESOME, PURPLE, PURPLE_LIGHT, 54),
        ft.Container(height=4),
        ft.Text(title_text, size=18, color=INK, weight=ft.FontWeight.W_700),
        ft.Text(description, size=13, color=MUTED, text_align=ft.TextAlign.CENTER),
    ]
    if button:
        controls.extend([ft.Container(height=8), button])
    return surface(
        ft.Column(controls=controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
        padding=34,
    )


def chart_control(chart_payload: dict[str, Any], height: int = 270) -> ft.Control:
    chart_type = chart_payload.get("chart_type", "bar")
    raw_x = chart_payload.get("x", []) or []
    raw_y = chart_payload.get("y", []) or []
    values: list[float] = []
    for value in raw_y:
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            values.append(0.0)
    if not values and chart_type != "histogram":
        return empty_state("Not enough chart data", "Choose a numeric measure to draw this visual.")

    if chart_type == "pie":
        palette = [PURPLE, MINT, ORANGE, BLUE, "#D46EF5", "#F2C94C", "#6FCF97", "#56CCF2"]
        chart = fch.PieChart(
            sections=[
                fch.PieChartSection(
                    value=value,
                    title=str(raw_x[index])[:14],
                    color=palette[index % len(palette)],
                    radius=86,
                )
                for index, value in enumerate(values[:12])
            ],
            center_space_radius=42,
            sections_space=3,
            height=height,
        )
    elif chart_type == "line" or chart_type == "scatter":
        points = [fch.LineChartDataPoint(x=index, y=value) for index, value in enumerate(values)]
        chart = fch.LineChart(
            data_series=[
                fch.LineChartData(
                    points=points,
                    color=PURPLE,
                    stroke_width=3,
                    curved=chart_type == "line",
                    point=True,
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_CENTER,
                        end=ft.Alignment.BOTTOM_CENTER,
                        colors=["#7C5CFC55", "#7C5CFC05"],
                    ),
                )
            ],
            min_x=0,
            max_x=max(len(points) - 1, 1),
            min_y=0,
            max_y=max(max(values) * 1.2, 1),
            height=height,
            horizontal_grid_lines=fch.ChartGridLines(color=LINE, width=1, dash_pattern=[3, 4]),
        )
    else:
        groups = [
            fch.BarChartGroup(
                x=index,
                rods=[
                    fch.BarChartRod(from_y=0, to_y=value, color=PURPLE, width=22, border_radius=5)
                ],
            )
            for index, value in enumerate(values[:24])
        ]
        chart = fch.BarChart(
            groups=groups,
            max_y=max(max(values) * 1.2, 1),
            min_y=0,
            height=height,
            interactive=True,
            horizontal_grid_lines=fch.ChartGridLines(color=LINE, width=1, dash_pattern=[3, 4]),
        )
    return chart


def chart_card(name: str, chart_payload: dict[str, Any], subtitle: str = "") -> ft.Container:
    return surface(
        ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(name, size=16, color=INK, weight=ft.FontWeight.W_700),
                                label(subtitle, 12, MUTED),
                            ],
                            spacing=2,
                        ),
                        ft.Container(expand=True),
                        icon_box(ft.Icons.INSIGHTS, PURPLE, PURPLE_LIGHT, 38),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=10),
                chart_control(chart_payload),
            ],
            spacing=3,
        ),
        padding=20,
    )


def dataset_table(
    preview: list[dict[str, Any]], max_rows: int = 12, compact: bool = False
) -> ft.Container:
    if not preview:
        return empty_state(
            "No preview yet", "Upload a workbook or choose a sheet to inspect the rows."
        )
    columns = list(preview[0].keys())[:8]
    rows = []
    for record in preview[:max_rows]:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(
                            _display_value(record.get(column)),
                            size=11 if compact else 12,
                            color=INK,
                            no_wrap=True,
                        )
                    )
                    for column in columns
                ]
            )
        )
    table = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text(column, size=12, color=MUTED, weight=ft.FontWeight.W_700))
            for column in columns
        ],
        rows=rows,
        heading_row_color=BG,
        data_row_min_height=36 if compact else 44,
        data_row_max_height=44 if compact else 56,
        divider_thickness=1,
        column_spacing=18 if compact else 26,
    )
    return ft.Container(content=ft.Row([table], scroll=ft.ScrollMode.AUTO), padding=0)


def _display_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}" if value % 1 else f"{value:,.0f}"
    return str(value)[:36]


def profile_rows(profile: dict[str, Any]) -> ft.Column:
    items = profile.get("column_profiles", [])[:8]
    controls = []
    for item in items:
        nulls = item.get("nulls", 0)
        color = RED if nulls else MINT
        controls.append(
            ft.Row(
                [
                    ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
                    ft.Text(item.get("name", "column"), color=INK, size=12, expand=True),
                    label(item.get("dtype", ""), 11, MUTED),
                    label(f"{nulls} empty", 11, color),
                ],
                spacing=8,
            )
        )
    return ft.Column(controls=controls or [label("No columns detected", 12, MUTED)], spacing=12)


def app_avatar(name: str, size: int = 38) -> ft.Container:
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "IF"
    return ft.Container(
        content=ft.Text(initials, size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
        width=size,
        height=size,
        alignment=ft.Alignment.CENTER,
        bgcolor=PURPLE,
        border_radius=size / 2,
    )
