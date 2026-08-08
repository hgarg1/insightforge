"""Visual language for InsightForge."""

from __future__ import annotations

import flet as ft

BG = "#F6F7FC"
PANEL = "#FFFFFF"
INK = "#172033"
MUTED = "#68778E"
LINE = "#E4E8F1"
NAVY = "#151D2F"
NAVY_2 = "#202B43"
PURPLE = "#7057F5"
PURPLE_LIGHT = "#EFECFF"
MINT = "#23C4A0"
MINT_LIGHT = "#E1F8F2"
ORANGE = "#F29E4C"
ORANGE_LIGHT = "#FFF1E2"
BLUE = "#5E8BFF"
BLUE_LIGHT = "#E8EEFF"
RED = "#E56B74"


def app_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme_seed=PURPLE,
        visual_density=ft.VisualDensity.COMFORTABLE,
        font_family="Aptos",
        use_material3=True,
    )


def surface(
    content: ft.Control, padding: int | float = 22, width: int | float | None = None
) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        width=width,
        bgcolor=PANEL,
        border=ft.Border.all(1, LINE),
        border_radius=20,
        shadow=ft.BoxShadow(
            blur_radius=24,
            spread_radius=-8,
            color="#17203312",
            offset=ft.Offset(0, 8),
        ),
    )


def label(
    value: str, size: int = 12, color: str = MUTED, weight: ft.FontWeight | None = None
) -> ft.Text:
    return ft.Text(value, size=size, color=color, weight=weight)


def title(value: str, size: int = 28) -> ft.Text:
    return ft.Text(value, size=size, color=INK, weight=ft.FontWeight.W_700)


def primary_button(
    value: str,
    on_click,
    icon=None,
    width: int | float | None = None,
    disabled: bool = False,
) -> ft.Button:
    return ft.Button(
        content=value,
        icon=icon,
        on_click=on_click,
        width=width,
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor=PURPLE,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=13),
            padding=ft.Padding.symmetric(horizontal=19, vertical=15),
            elevation=0,
        ),
    )


def secondary_button(value: str, on_click, icon=None, disabled: bool = False) -> ft.Button:
    return ft.Button(
        content=value,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.TRANSPARENT,
            color=INK,
            side=ft.BorderSide(1, LINE),
            shape=ft.RoundedRectangleBorder(radius=13),
            padding=ft.Padding.symmetric(horizontal=16, vertical=13),
        ),
    )


def icon_box(
    icon, color: str = PURPLE, background: str = PURPLE_LIGHT, size: int = 42
) -> ft.Container:
    return ft.Container(
        content=ft.Icon(icon, color=color, size=21),
        width=size,
        height=size,
        alignment=ft.Alignment.CENTER,
        bgcolor=background,
        border_radius=13,
    )


def divider() -> ft.Divider:
    return ft.Divider(height=1, thickness=1, color=LINE)
