"""Shared Windows/web Flet application for InsightForge."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import flet as ft

from insightforge.core.security import (
    PASSWORD_REQUIREMENTS,
    password_requirement_status,
    password_requirements,
)
from insightforge.ui.client import ApiClient, ApiError
from insightforge.ui.components import (
    app_avatar,
    brand_mark,
    chart_card,
    dataset_table,
    empty_state,
    insight_card,
    profile_rows,
    stat_card,
)
from insightforge.ui.theme import (
    BG,
    BLUE,
    BLUE_LIGHT,
    INK,
    LINE,
    MINT,
    MINT_LIGHT,
    MUTED,
    NAVY,
    ORANGE,
    ORANGE_LIGHT,
    PANEL,
    PURPLE,
    PURPLE_LIGHT,
    RED,
    app_theme,
    divider,
    icon_box,
    label,
    primary_button,
    secondary_button,
    surface,
    title,
)


class AuthView:
    def __init__(
        self, page: ft.Page, client: ApiClient, on_authenticated: Callable[[dict[str, Any]], None]
    ):
        self.page = page
        self.client = client
        self.on_authenticated = on_authenticated
        self.mode = "login"
        self.error = ""
        self.notice = ""
        self.reset_token = ""
        self.busy = False
        self.viewport_width: float | None = None
        self.email = ft.TextField(
            label="Work email",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            autofocus=True,
            border_radius=13,
            border_color=LINE,
            focused_border_color=PURPLE,
            bgcolor=PANEL,
        )
        self.name = ft.TextField(
            label="Full name",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=13,
            border_color=LINE,
            focused_border_color=PURPLE,
            bgcolor=PANEL,
        )
        self.password = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            on_change=self._update_password_checklist,
            border_radius=13,
            border_color=LINE,
            focused_border_color=PURPLE,
            bgcolor=PANEL,
        )
        self.confirm = ft.TextField(
            label="Confirm password",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            border_radius=13,
            border_color=LINE,
            focused_border_color=PURPLE,
            bgcolor=PANEL,
        )
        self.token = ft.TextField(
            label="Reset token",
            prefix_icon=ft.Icons.KEY,
            value="",
            border_radius=13,
            border_color=LINE,
            focused_border_color=PURPLE,
            bgcolor=PANEL,
        )
        self.password_checklist = ft.Column(spacing=5)
        self.form_width = 430

    def _compact_auth_layout(self) -> bool:
        width = self.viewport_width or getattr(self.page, "width", 0) or 0
        return 0 < width < 1050

    def _auth_form_width(self) -> int:
        width = self.viewport_width or getattr(self.page, "width", 0) or 0
        if width <= 0:
            return self.form_width
        side_padding = 20 if self._compact_auth_layout() else 46
        return min(self.form_width, max(280, int(width - side_padding * 2 - 36)))

    def render(self) -> ft.Control:
        compact = self._compact_auth_layout()
        form_width = self._auth_form_width()
        hero = ft.Container(
            width=430,
            visible=not compact,
            col={"xs": 12, "sm": 12, "md": 12, "lg": 5},
            padding=42,
            bgcolor=NAVY,
            border_radius=24,
            content=ft.Column(
                controls=[
                    brand_mark(light=True),
                    ft.Container(expand=True),
                    ft.Text(
                        "Make every workbook\nfeel like a conversation.",
                        size=34,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_700,
                    ),
                    ft.Container(height=12),
                    ft.Text(
                        "A calmer, clearer command center for the decisions hiding inside your spreadsheets.",
                        size=15,
                        color="#B9C3D6",
                        max_lines=3,
                    ),
                    ft.Container(height=28),
                    self._hero_signal(
                        "01",
                        "See the shape of your data",
                        "Quality signals before you build a chart.",
                    ),
                    self._hero_signal(
                        "02",
                        "Turn patterns into proof",
                        "Visuals that explain what changed and why.",
                    ),
                    self._hero_signal(
                        "03",
                        "Save your point of view",
                        "Dashboards that stay yours and evolve with you.",
                    ),
                    ft.Container(expand=True),
                    label(
                        "PRIVATE BY DEFAULT  ·  LOCAL-FIRST  ·  EXPORTABLE",
                        10,
                        "#7F8DA6",
                        ft.FontWeight.W_600,
                    ),
                ],
                spacing=14,
            ),
        )
        form = ft.Container(
            expand=True,
            col={"xs": 12, "sm": 12, "md": 12, "lg": 12 if compact else 7},
            padding=ft.Padding.symmetric(horizontal=20 if compact else 46, vertical=30),
            content=ft.Column(
                controls=[
                    ft.Container(expand=True if not compact else False, height=8 if compact else None),
                    *(
                        [
                            ft.Row(
                                [brand_mark()],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(height=14),
                        ]
                        if compact
                        else []
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=self._form_content(),
                                width=form_width + (40 if compact else 64),
                                padding=20 if compact else 32,
                                bgcolor=PANEL,
                                border=ft.Border.all(1, LINE),
                                border_radius=24,
                                shadow=ft.BoxShadow(
                                    blur_radius=32,
                                    spread_radius=-10,
                                    color="#1720331A",
                                    offset=ft.Offset(0, 12),
                                ),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(expand=True if not compact else False, height=16 if compact else None),
                    ft.Row(
                        [
                            label("InsightForge v0.1  ·  Built for curious teams", 11, MUTED),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                # Keep the brand panel anchored while longer auth flows own
                # their overflow. Signup, reset confirmation, and validation
                # notices can all exceed a short desktop/browser viewport.
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
            ),
        )
        return ft.Container(
            expand=True,
            bgcolor=BG,
            padding=10 if compact else 18,
            content=ft.ResponsiveRow(
                controls=[hero, form],
                expand=True,
                spacing=18,
                run_spacing=12,
            ),
        )

    def _hero_signal(self, number: str, heading: str, detail: str) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Text(number, size=12, color="#A995FF", weight=ft.FontWeight.W_700),
                ft.Column(
                    [
                        ft.Text(
                            heading, size=13, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600
                        ),
                        label(detail, 11, "#9BA8BE"),
                    ],
                    spacing=2,
                ),
            ],
            spacing=12,
        )

    def _form_content(self) -> ft.Control:
        field_width = self._auth_form_width()
        for field in (self.email, self.name, self.password, self.confirm, self.token):
            field.width = field_width
        if self.mode == "reset-request":
            eyebrow, heading, subheading = (
                "ACCOUNT RECOVERY",
                "Reset your password",
                "We will prepare a secure, time-limited reset link.",
            )
        elif self.mode == "reset-confirm":
            eyebrow, heading, subheading = (
                "ACCOUNT RECOVERY",
                "Choose a new password",
                "Your reset link is ready. Create a password you will remember.",
            )
        elif self.mode == "signup":
            eyebrow, heading, subheading = (
                "WELCOME TO THE FORGE",
                "Create your workspace",
                "Start with a clean canvas for your next decision.",
            )
        else:
            eyebrow, heading, subheading = (
                "WELCOME BACK",
                "Sign in to your workspace",
                "Your next clear answer is closer than it looks.",
            )

        controls: list[ft.Control] = [
            label(eyebrow, 11, PURPLE, ft.FontWeight.W_700),
            ft.Text(
                heading,
                size=27 if self._compact_auth_layout() else 31,
                color=INK,
                weight=ft.FontWeight.W_700,
            ),
            label(subheading, 14, MUTED),
            ft.Container(height=12),
        ]
        if self.mode == "signup":
            controls.append(self.name)
        if self.mode in {"login", "signup", "reset-request"}:
            controls.append(self.email)
        if self.mode == "reset-confirm":
            self.token.value = self.reset_token or self.token.value
            controls.append(self.token)
        if self.mode in {"login", "signup", "reset-confirm"}:
            controls.append(self.password)
        if self.mode in {"signup", "reset-confirm"}:
            self._populate_password_checklist()
            controls.append(self.password_checklist)
        if self.mode in {"signup", "reset-confirm"}:
            controls.append(self.confirm)
        if self.error:
            controls.extend(
                [
                    ft.Container(height=2),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.ERROR_OUTLINE, color=RED, size=17),
                                ft.Text(
                                    self.error,
                                    size=12,
                                    color=INK,
                                    expand=True,
                                    max_lines=3,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        bgcolor="#FCEBED",
                        border_radius=10,
                        padding=10,
                    ),
                ]
            )
        if self.notice:
            controls.extend(
                [
                    ft.Container(height=2),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=MINT, size=17),
                                ft.Text(
                                    self.notice,
                                    size=12,
                                    color=INK,
                                    expand=True,
                                    max_lines=3,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        bgcolor=MINT_LIGHT,
                        border_radius=10,
                        padding=10,
                    ),
                ]
            )
        if self.mode == "login":
            controls.extend(
                [
                    ft.Row(
                        [
                            ft.Checkbox(label="Keep me signed in", value=True),
                            ft.Container(expand=True),
                            self._link("Forgot password?", self._show_reset_request),
                        ]
                    ),
                    primary_button(
                        "Signing in…" if self.busy else "Sign in",
                        self._submit,
                        ft.Icons.ARROW_FORWARD,
                        width=self._auth_form_width(),
                        disabled=self.busy,
                    ),
                    ft.Row(
                        [
                            label("New to InsightForge?", 12, MUTED),
                            self._link("Create an account", self._show_signup),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ]
            )
        elif self.mode == "signup":
            controls.extend(
                [
                    primary_button(
                        "Creating workspace…" if self.busy else "Create workspace",
                        self._submit,
                        ft.Icons.ARROW_FORWARD,
                        width=self._auth_form_width(),
                        disabled=self.busy,
                    ),
                    ft.Row(
                        [
                            label("Already have a workspace?", 12, MUTED),
                            self._link("Sign in", self._show_login),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ]
            )
        elif self.mode == "reset-request":
            controls.extend(
                [
                    primary_button(
                        "Preparing reset link…" if self.busy else "Prepare reset link",
                        self._submit,
                        ft.Icons.MAIL_OUTLINED,
                        width=self._auth_form_width(),
                        disabled=self.busy,
                    ),
                    ft.Row(
                        [self._link("Back to sign in", self._show_login)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ]
            )
        else:
            controls.extend(
                [
                    primary_button(
                        "Updating password…" if self.busy else "Update password",
                        self._submit,
                        ft.Icons.LOCK_RESET,
                        width=self._auth_form_width(),
                        disabled=self.busy,
                    ),
                    ft.Row(
                        [self._link("Back to sign in", self._show_login)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ]
            )
        return ft.Column(controls=controls, spacing=14)

    def _populate_password_checklist(self) -> None:
        value = self.password.value or ""
        status = password_requirement_status(value)
        complete = sum(status.values())
        controls: list[ft.Control] = [
            label(
                f"PASSWORD REQUIREMENTS  ·  {complete}/{len(PASSWORD_REQUIREMENTS)} MET",
                10,
                PURPLE if complete == len(PASSWORD_REQUIREMENTS) else MUTED,
                ft.FontWeight.W_700,
            )
        ]
        for key, requirement in PASSWORD_REQUIREMENTS:
            passed = status[key]
            color = MINT if passed else RED if value else MUTED
            controls.append(
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if passed else ft.Icons.CIRCLE_OUTLINED,
                            size=15,
                            color=color,
                        ),
                        label(requirement.capitalize(), 11, color),
                    ],
                    spacing=7,
                )
            )
        self.password_checklist.controls = controls

    def _update_password_checklist(self, _=None) -> None:
        # The checklist is intentionally not mounted on the login screen. Calling
        # update() on that detached Column crashes the Flet web session while the
        # user types their password.
        if self.mode not in {"signup", "reset-confirm"}:
            return
        self._populate_password_checklist()
        self.password_checklist.update()

    def _link(self, value: str, handler) -> ft.TextButton:
        return ft.TextButton(
            content=value,
            on_click=handler,
            style=ft.ButtonStyle(
                color=PURPLE,
                overlay_color=ft.Colors.TRANSPARENT,
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            ),
        )

    def _reset_message(self) -> None:
        self.error = ""
        self.notice = ""

    def _render_auth(self) -> None:
        self.page.controls.clear()
        self.page.add(self.render())
        self.page.update()

    def _show_login(self, _=None) -> None:
        self.mode = "login"
        self._reset_message()
        self._render_auth()

    def _show_signup(self, _=None) -> None:
        self.mode = "signup"
        self._reset_message()
        self._render_auth()

    def _show_reset_request(self, _=None) -> None:
        self.mode = "reset-request"
        self._reset_message()
        self._render_auth()

    async def _submit(self, _=None) -> None:
        if self.busy:
            return
        self._reset_message()
        try:
            if self.mode == "login":
                if not self.email.value or not self.password.value:
                    raise ApiError("Enter your email and password to continue.")
            elif self.mode == "signup":
                if self.password.value != self.confirm.value:
                    raise ApiError("Your passwords do not match.")
                if password_requirements(self.password.value or ""):
                    raise ApiError("Meet every password requirement before continuing.")
            elif self.mode == "reset-confirm" and self.password.value != self.confirm.value:
                raise ApiError("Your passwords do not match.")
            elif self.mode == "reset-confirm" and password_requirements(self.password.value or ""):
                raise ApiError("Meet every password requirement before continuing.")
        except ApiError as exc:
            self.error = exc.message
            self._render_auth()
            return

        self.busy = True
        self._render_auth()
        try:
            if self.mode == "login":
                payload = await asyncio.to_thread(
                    self.client.login, self.email.value.strip(), self.password.value
                )
                self.busy = False
                self.on_authenticated(payload["user"])
                return
            if self.mode == "signup":
                payload = await asyncio.to_thread(
                    self.client.signup,
                    self.email.value.strip(),
                    self.name.value.strip(),
                    self.password.value,
                )
                self.busy = False
                self.on_authenticated(payload["user"])
                return
            if self.mode == "reset-request":
                result = await asyncio.to_thread(self.client.request_reset, self.email.value.strip())
                if result.get("development_token"):
                    self.reset_token = result["development_token"]
                    self.notice = "Development mode prepared a one-time token. Continue below to set your password."
                    self.mode = "reset-confirm"
                else:
                    self.notice = result.get("message", "Check your inbox for the next step.")
                return
            result = await asyncio.to_thread(
                self.client.confirm_reset, self.token.value.strip(), self.password.value
            )
            self.notice = result.get("message", "Password updated.")
            self.mode = "login"
        except ApiError as exc:
            self.error = exc.message
        finally:
            self.busy = False
            if not self.client.authenticated:
                self._render_auth()


class InsightForgeApp:
    def __init__(
        self,
        page: ft.Page,
        client: ApiClient | None = None,
        initial_auth_mode: str = "login",
    ):
        self.page = page
        self.client = client or ApiClient()
        self.page.title = "InsightForge"
        self.page.theme = app_theme()
        self.page.bgcolor = BG
        self.page.padding = 0
        if not self.page.web:
            self.page.window_min_width = 1040
            self.page.window_min_height = 720
        # FilePicker is a Flet service, not a visual overlay control. Registering
        # it in ``page.overlay`` makes the web runtime try to deserialize it as
        # a regular control and produces: "Unknown control: FilePicker".
        self.file_picker = ft.FilePicker()
        self.page.services.append(self.file_picker)
        self.save_picker = ft.FilePicker()
        self.page.services.append(self.save_picker)
        self.current_view = "Overview"
        self.datasets: list[dict[str, Any]] = []
        self.active_dataset: dict[str, Any] | None = None
        self.dataset_profiles: dict[str, dict[str, Any]] = {}
        self.dashboard: dict[str, Any] = {"name": "My command center", "widgets": []}
        self.visualizations: list[dict[str, Any]] = []
        self.preview: list[dict[str, Any]] = []
        self.transformed: dict[str, Any] | None = None
        self.last_chart: dict[str, Any] | None = None
        self.visual_draft: dict[str, str] = {}
        self.customizing = False
        self.status = ""
        self.status_kind = "info"
        self.busy = False
        self.busy_message = ""
        self.compact_tables = False
        self.show_suggestions = True
        self.auth = AuthView(page, self.client, self.authenticated)
        self.auth.mode = initial_auth_mode
        self._responsive_width: float | None = None
        self._last_layout_mode = self._layout_mode()
        self.page.on_resize = self._handle_resize
        self.page.add(self.auth.render())

    def authenticated(self, _user: dict[str, Any]) -> None:
        self.status = ""
        self.status_kind = "info"
        try:
            self.datasets = self.client.datasets()
            self.dashboard = self.client.dashboard()
            self.visualizations = self.client.visualizations()
            if self.datasets:
                self.select_dataset(self.datasets[0]["id"], refresh=False)
        except ApiError as exc:
            self._set_status(exc.message, "error")
        self._render_shell()

    def _render_shell(self) -> None:
        self.page.controls.clear()
        if self._mobile_layout():
            shell = ft.Column(
                [self._header(), self._content(), self._bottom_nav()],
                expand=True,
                spacing=0,
            )
        else:
            shell = ft.Row(
                [
                    self._sidebar(),
                    ft.Container(
                        expand=True,
                        content=ft.Column([self._header(), self._content()], spacing=0),
                    ),
                ],
                expand=True,
                spacing=0,
            )
        self.page.add(shell)
        self.page.update()

    def _sidebar(self) -> ft.Container:
        compact = self._compact_layout()
        items = [
            ("Overview", ft.Icons.DASHBOARD),
            ("Data Lab", ft.Icons.DATA_EXPLORATION),
            ("Visuals", ft.Icons.BAR_CHART),
            ("Settings", ft.Icons.SETTINGS),
        ]
        nav_controls: list[ft.Control] = [
            brand_mark(light=True, compact=compact),
            ft.Container(height=36),
        ]
        for name, icon in items:
            active = name == self.current_view
            nav_controls.append(
                ft.Button(
                    content=(
                        ft.Icon(icon, color="#FFFFFF" if active else "#93A0B8", size=18)
                        if compact
                        else ft.Row(
                            [
                                ft.Icon(icon, color="#FFFFFF" if active else "#93A0B8", size=18),
                                ft.Text(
                                    name,
                                    color="#FFFFFF" if active else "#93A0B8",
                                    size=13,
                                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
                                ),
                            ],
                            spacing=13,
                        )
                    ),
                    on_click=lambda _, selected=name: self.navigate(selected),
                    tooltip=name if compact else None,
                    style=ft.ButtonStyle(
                        bgcolor=PURPLE if active else ft.Colors.TRANSPARENT,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.Padding.symmetric(
                            horizontal=14 if not compact else 12, vertical=13
                        ),
                    ),
                )
            )
        nav_controls.extend(
            [
                ft.Container(expand=True),
                divider(),
                ft.Button(
                    content=(
                        ft.Icon(ft.Icons.LOGOUT, color="#93A0B8", size=18)
                        if compact
                        else ft.Row(
                            [
                                ft.Icon(ft.Icons.LOGOUT, color="#93A0B8", size=18),
                                ft.Text("Sign out", color="#93A0B8", size=13),
                            ],
                            spacing=13,
                        )
                    ),
                    on_click=self.sign_out,
                    tooltip="Sign out" if compact else None,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.TRANSPARENT,
                        padding=ft.Padding.symmetric(
                            horizontal=14 if not compact else 12, vertical=13
                        ),
                    ),
                ),
                *(
                    []
                    if compact
                    else [label("INSIGHTFORGE  /  0.1", 9, "#66748D", ft.FontWeight.W_600)]
                ),
            ]
        )
        return ft.Container(
            width=82 if compact else 244,
            bgcolor=NAVY,
            padding=14 if compact else 18,
            content=ft.Column(nav_controls, spacing=7),
        )

    def _bottom_nav(self) -> ft.Container:
        items = [
            ("Overview", ft.Icons.DASHBOARD_OUTLINED),
            ("Data Lab", ft.Icons.DATA_EXPLORATION_OUTLINED),
            ("Visuals", ft.Icons.BAR_CHART_OUTLINED),
            ("Settings", ft.Icons.SETTINGS_OUTLINED),
        ]
        controls: list[ft.Control] = []
        for name, icon in items:
            active = name == self.current_view
            controls.append(
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(horizontal=4, vertical=8),
                    border_radius=14,
                    bgcolor=PURPLE_LIGHT if active else ft.Colors.TRANSPARENT,
                    on_click=lambda _, selected=name: self.navigate(selected),
                    content=ft.Column(
                        [
                            ft.Icon(icon, size=20, color=PURPLE if active else MUTED),
                            ft.Text(
                                "Lab" if name == "Data Lab" else name,
                                size=10,
                                color=PURPLE if active else MUTED,
                                weight=ft.FontWeight.W_700 if active else ft.FontWeight.W_500,
                            ),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        return ft.Container(
            height=72,
            bgcolor=PANEL,
            border=ft.Border(top=ft.BorderSide(1, LINE)),
            padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            content=ft.Row(controls, spacing=6),
        )

    def _header(self) -> ft.Container:
        user = self.client.user or {}
        if self._mobile_layout():
            return ft.Container(
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                bgcolor=PANEL,
                border=ft.Border(bottom=ft.BorderSide(1, LINE)),
                content=ft.Row(
                    [
                        brand_mark(compact=True),
                        ft.Column(
                            [
                                ft.Text(
                                    self.current_view,
                                    size=15,
                                    color=INK,
                                    weight=ft.FontWeight.W_700,
                                ),
                                label("InsightForge workspace", 10, MUTED),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        app_avatar(user.get("full_name", "Insight Forge"), 36),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        search = ft.TextField(
            hint_text="Search workbooks, insights, or commands",
            prefix_icon=ft.Icons.SEARCH,
            width=280 if self._compact_layout() else 360,
            height=44,
            border_radius=13,
            border_color=LINE,
            bgcolor=PANEL,
            on_submit=self.run_search,
        )
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=28, vertical=17),
            bgcolor=BG,
            content=ft.Row(
                [
                    search,
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.NOTIFICATIONS_NONE,
                        icon_color=MUTED,
                        tooltip="Notifications",
                        on_click=self.show_notifications,
                    ),
                    ft.Container(width=1, height=28, bgcolor=LINE),
                    app_avatar(user.get("full_name", "Insight Forge")),
                    ft.Column(
                        [
                            ft.Text(
                                user.get("full_name", "Explorer"),
                                size=12,
                                color=INK,
                                weight=ft.FontWeight.W_600,
                            ),
                            label(user.get("plan", "Creator"), 10, MUTED),
                        ],
                        spacing=2,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    def _content(self) -> ft.Container:
        content = {
            "Overview": self._overview,
            "Data Lab": self._data_lab,
            "Visuals": self._visuals,
            "Settings": self._settings,
        }[self.current_view]()
        content_controls: list[ft.Control] = []
        if self.status:
            status_color = (
                RED
                if self.status_kind == "error"
                else MINT
                if self.status_kind == "success"
                else PURPLE
            )
            status_background = (
                "#FCEBED"
                if self.status_kind == "error"
                else MINT_LIGHT
                if self.status_kind == "success"
                else PURPLE_LIGHT
            )
            content_controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.ERROR_OUTLINE
                                if self.status_kind == "error"
                                else ft.Icons.CHECK_CIRCLE_OUTLINE
                                if self.status_kind == "success"
                                else ft.Icons.INFO_OUTLINE,
                                color=status_color,
                                size=17,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Couldn’t complete that"
                                        if self.status_kind == "error"
                                        else "All set"
                                        if self.status_kind == "success"
                                        else "Workspace update",
                                        size=12,
                                        color=INK,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    ft.Text(
                                        self.status,
                                        size=12,
                                        color=INK,
                                        max_lines=3,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=MUTED,
                                icon_size=16,
                                tooltip="Dismiss",
                                on_click=lambda _: self._clear_status(),
                            ),
                        ],
                        spacing=8,
                    ),
                    bgcolor=status_background,
                    border_radius=10,
                    padding=12,
                )
            )
            content_controls.append(ft.Container(height=10))
        content_controls.append(content)
        return ft.Container(
            expand=True,
            bgcolor=BG,
            padding=ft.Padding.symmetric(
                horizontal=16 if self._mobile_layout() else 24 if self._compact_layout() else 32,
                vertical=14 if self._mobile_layout() else 12,
            ),
            content=ft.Column(content_controls, scroll=ft.ScrollMode.AUTO, expand=True),
        )

    def _compact_layout(self) -> bool:
        width = self._responsive_width or getattr(self.page, "width", 0) or 0
        return 0 < width < 1080

    def _mobile_layout(self) -> bool:
        width = self._responsive_width or getattr(self.page, "width", 0) or 0
        return 0 < width < 680

    def _layout_mode(self) -> str:
        if self._mobile_layout():
            return "mobile"
        if self._compact_layout():
            return "compact"
        return "wide"

    def _handle_resize(self, event: ft.ControlEvent | None = None) -> None:
        if event is not None and hasattr(event, "width"):
            self._responsive_width = event.width
            self.auth.viewport_width = event.width
        layout_mode = self._layout_mode()
        if layout_mode == self._last_layout_mode:
            return
        self._last_layout_mode = layout_mode
        if self.client.authenticated:
            self._render_shell()
        else:
            self.page.controls.clear()
            self.page.add(self.auth.render())
            self.page.update()

    def _set_status(self, message: str, kind: str = "info") -> None:
        self.status = message
        self.status_kind = kind

    def _clear_status(self) -> None:
        self.status = ""
        self.status_kind = "info"
        self._render_shell()

    def show_notifications(self, _=None) -> None:
        self._set_status("You are all caught up.", "success")
        self._render_shell()

    def run_search(self, event: ft.ControlEvent) -> None:
        query = (event.control.value or "").strip().lower()
        if not query:
            self._set_status("Search your workbooks, insights, or commands from here.")
        elif any(term in query for term in ("data", "workbook", "table")):
            self.current_view = "Data Lab"
            self._set_status("Opened Data Lab.", "success")
        elif any(term in query for term in ("visual", "chart", "graph")):
            self.current_view = "Visuals"
            self._set_status("Opened Visual Studio.", "success")
        elif any(term in query for term in ("setting", "profile", "privacy")):
            self.current_view = "Settings"
            self._set_status("Opened workspace settings.", "success")
        else:
            self._set_status(f"No command matched “{query}”. Try “Data Lab” or “Visuals”.")
        self._render_shell()

    def navigate(self, name: str) -> None:
        self.current_view = name
        self._render_shell()

    def _screen_header(
        self,
        eyebrow: str,
        heading: str,
        description: str,
        actions: list[ft.Control] | None = None,
    ) -> ft.Control:
        viewport_width = self._responsive_width or getattr(self.page, "width", 0) or 0
        mobile_width = max(280, int(viewport_width - 32)) if viewport_width else None
        copy = ft.Column(
            [
                label(eyebrow, 11, PURPLE, ft.FontWeight.W_700),
                ft.Text(
                    heading,
                    size=25 if self._mobile_layout() else 28,
                    color=INK,
                    weight=ft.FontWeight.W_700,
                    width=mobile_width if self._mobile_layout() else None,
                    max_lines=2,
                ),
                ft.Text(
                    description,
                    size=13,
                    color=MUTED,
                    width=mobile_width if self._mobile_layout() else None,
                    max_lines=3,
                ),
            ],
            spacing=4,
            expand=not self._mobile_layout(),
            width=mobile_width if self._mobile_layout() else None,
        )
        action_controls = actions or []
        if self._mobile_layout():
            return ft.Column(
                [
                    copy,
                    *(
                        [
                            ft.Container(height=8),
                            ft.Row(action_controls, wrap=True, spacing=10, run_spacing=10),
                        ]
                        if action_controls
                        else []
                    ),
                ],
                spacing=0,
            )
        return ft.Row(
            [copy, *action_controls],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _stat_grid(self, cards: list[ft.Control]) -> ft.ResponsiveRow:
        return ft.ResponsiveRow(
            [
                ft.Container(
                    content=card,
                    col={"xs": 12, "sm": 6, "lg": 6, "xl": 3},
                )
                for card in cards
            ],
            spacing=14,
            run_spacing=14,
        )

    def sign_out(self, _=None) -> None:
        self.client.logout()
        self.current_view = "Overview"
        self.page.controls.clear()
        self.page.add(self.auth.render())
        self.page.update()

    def _overview(self) -> ft.Control:
        user = self.client.user or {}
        first = (user.get("full_name") or "Explorer").split()[0]
        latest = self.active_dataset
        header = self._screen_header(
            "YOUR COMMAND CENTER",
            f"Good morning, {first}.",
            "The clearest path from spreadsheet to signal starts here.",
            [
                secondary_button("Customize", self.toggle_customizing, ft.Icons.EDIT),
                primary_button(
                    "Upload workbook",
                    self.open_picker,
                    ft.Icons.CLOUD_UPLOAD,
                    disabled=self.busy,
                ),
            ],
        )
        if latest:
            stats = self._stat_grid(
                [
                    stat_card(
                        ft.Icons.CHECK_CIRCLE,
                        "Dataset health",
                        f"{latest.get('quality_score', 0):.0f}%",
                        "Quality score",
                        MINT,
                        MINT_LIGHT,
                    ),
                    stat_card(
                        ft.Icons.TABLE_VIEW,
                        "Rows explored",
                        f"{latest.get('row_count', 0):,}",
                        f"Across {latest.get('column_count', 0)} columns",
                        PURPLE,
                        PURPLE_LIGHT,
                    ),
                    stat_card(
                        ft.Icons.AUTO_AWESOME,
                        "Saved visuals",
                        str(len(self.visualizations)),
                        "Ready for your dashboard",
                        ORANGE,
                        ORANGE_LIGHT,
                    ),
                    stat_card(
                        ft.Icons.FILE_PRESENT,
                        "Workbooks",
                        str(len(self.datasets)),
                        "Private to this workspace",
                        BLUE,
                        BLUE_LIGHT,
                    ),
                ],
            )
            upload = self._upload_banner(latest)
            widgets = self._widget_grid()
            return ft.Column(
                [
                    header,
                    ft.Container(height=20),
                    stats,
                    ft.Container(height=20),
                    upload,
                    ft.Container(height=20),
                    widgets,
                ],
                spacing=0,
            )
        upload = self._upload_banner(None)
        return ft.Column(
            [
                header,
                ft.Container(height=28),
                upload,
                ft.Container(height=24),
                self._starter_grid()
                if self.show_suggestions
                else surface(
                    ft.Row(
                        [
                            icon_box(ft.Icons.LIGHTBULB_OUTLINE, BLUE, BLUE_LIGHT),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Suggestions are paused",
                                        size=15,
                                        color=INK,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    label(
                                        "You can turn them back on any time from Settings.",
                                        12,
                                        MUTED,
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                        ],
                        spacing=14,
                    ),
                    padding=19,
                ),
            ],
            spacing=0,
        )

    def _upload_banner(self, dataset: dict[str, Any] | None) -> ft.Container:
        if dataset:
            heading = "Your workspace is warmed up."
            detail = f"{dataset.get('filename', 'Workbook')} is ready. Open Data Lab to profile it or build a visual that earns its place on the dashboard."
            action = ft.Button(
                content="Open Data Lab",
                icon=ft.Icons.DATA_EXPLORATION,
                on_click=lambda _: self.navigate("Data Lab"),
                disabled=self.busy,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor="#FFFFFF12",
                    side=ft.BorderSide(1, "#FFFFFF55"),
                    shape=ft.RoundedRectangleBorder(radius=13),
                    padding=ft.Padding.symmetric(horizontal=18, vertical=14),
                ),
            )
            accent = MINT
        else:
            heading = "Drop in a workbook. Find the story."
            detail = "Upload an Excel file and InsightForge will map its shape, flag quality gaps, and suggest your first useful visual."
            action = primary_button(
                "Choose Excel file",
                self.open_picker,
                ft.Icons.CLOUD_UPLOAD,
                disabled=self.busy,
            )
            accent = PURPLE
        return ft.Container(
            padding=20 if self._mobile_layout() else 26,
            bgcolor=NAVY,
            border_radius=20,
            content=(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        ft.Icons.AUTO_AWESOME,
                                        color=ft.Colors.WHITE,
                                        size=26,
                                    ),
                                    width=52,
                                    height=52,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=accent,
                                    border_radius=16,
                                ),
                                ft.Text(
                                    heading,
                                    size=20,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.W_700,
                                    expand=True,
                                ),
                            ],
                            spacing=14,
                        ),
                        ft.Text(detail, size=13, color="#C1CADB"),
                        ft.Container(height=4),
                        action,
                    ],
                    spacing=12,
                )
                if self._mobile_layout()
                else ft.Row(
                    [
                    ft.Container(
                        content=ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=30),
                        width=62,
                        height=62,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=accent,
                        border_radius=18,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                heading, size=21, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700
                            ),
                            ft.Text(detail, size=13, color="#B9C3D6", max_lines=3),
                        ],
                        spacing=7,
                        expand=True,
                    ),
                    action,
                    ],
                    spacing=18,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ),
        )

    def _starter_grid(self) -> ft.Control:
        starters = [
            (
                ft.Icons.DATA_EXPLORATION,
                "Profile your data",
                "See missing values, duplicates, types, and quality score before you chart.",
                PURPLE,
                PURPLE_LIGHT,
            ),
            (
                ft.Icons.BAR_CHART,
                "Build a visual",
                "Turn a column pair into a shareable, dashboard-ready visual in seconds.",
                MINT,
                MINT_LIGHT,
            ),
            (
                ft.Icons.AUTO_AWESOME,
                "Keep your point of view",
                "Save the insights that matter and shape a workspace that feels like yours.",
                ORANGE,
                ORANGE_LIGHT,
            ),
        ]
        return ft.ResponsiveRow(
            [
                ft.Container(
                    content=surface(
                    ft.Column(
                        [
                            icon_box(i, c, t),
                            ft.Container(height=12),
                            ft.Text(h, size=15, color=INK, weight=ft.FontWeight.W_700),
                            label(d, 12, MUTED),
                        ],
                        spacing=5,
                    ),
                    padding=19,
                    ),
                    col={"xs": 12, "sm": 6, "lg": 4},
                )
                for i, h, d, c, t in starters
            ],
            spacing=14,
            run_spacing=14,
        )

    def _widget_grid(self) -> ft.Control:
        widgets = self.dashboard.get("widgets", [])
        controls: list[ft.Control] = []
        for index, widget in enumerate(widgets):
            if widget.get("hidden"):
                continue
            visual = next(
                (
                    item
                    for item in self.visualizations
                    if item.get("id") == widget.get("visualization_id")
                ),
                None,
            )
            chart = (visual or {}).get("spec", {}).get("chart")
            card = (
                chart_card(
                    widget.get("title", "Saved visual"),
                    chart,
                    widget.get("subtitle", "Saved to your command center"),
                )
                if chart
                else insight_card(widget)
            )
            if self.customizing:
                card.content.controls.append(
                    ft.Row(
                        [
                            ft.Button(
                                content="Move up",
                                on_click=lambda _, i=index: self.move_widget(i, -1),
                                style=ft.ButtonStyle(
                                    color=PURPLE, bgcolor=ft.Colors.TRANSPARENT, padding=0
                                ),
                            ),
                            ft.Button(
                                content="Move down",
                                on_click=lambda _, i=index: self.move_widget(i, 1),
                                style=ft.ButtonStyle(
                                    color=PURPLE, bgcolor=ft.Colors.TRANSPARENT, padding=0
                                ),
                            ),
                            ft.Container(expand=True),
                            ft.Button(
                                content="Hide",
                                on_click=lambda _, i=index: self.hide_widget(i),
                                style=ft.ButtonStyle(
                                    color=RED, bgcolor=ft.Colors.TRANSPARENT, padding=0
                                ),
                            ),
                        ],
                        spacing=10,
                    )
                )
            card.width = None
            controls.append(
                ft.Container(
                    content=card,
                    col={"xs": 12, "sm": 6, "lg": 4},
                )
            )
        if not controls:
            controls = [
                empty_state(
                    "Your dashboard is intentionally quiet",
                    "Bring a card back from Settings or create a new visual.",
                )
            ]
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                label("SAVED POINTS OF VIEW", 11, PURPLE, ft.FontWeight.W_700),
                                ft.Text(
                                    self.dashboard.get("name", "My command center"),
                                    size=18,
                                    color=INK,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ],
                            spacing=3,
                        ),
                        ft.Container(expand=True),
                        label(f"{len(widgets)} cards", 12, MUTED),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=12),
                ft.ResponsiveRow(controls, spacing=14, run_spacing=14),
            ],
            spacing=0,
        )

    def restore_hidden_widgets(self, _=None) -> None:
        changed = False
        for widget in self.dashboard.get("widgets", []):
            if widget.get("hidden"):
                widget["hidden"] = False
                changed = True
        if changed:
            try:
                self.dashboard = self.client.save_dashboard(self.dashboard)
                self._set_status("Hidden dashboard cards are visible again.", "success")
            except ApiError as exc:
                self._set_status(exc.message, "error")
        self._render_shell()

    def toggle_customizing(self, _=None) -> None:
        self.customizing = not self.customizing
        self._render_shell()

    def move_widget(self, index: int, direction: int) -> None:
        widgets = self.dashboard.get("widgets", [])
        target = index + direction
        if 0 <= target < len(widgets):
            widgets[index], widgets[target] = widgets[target], widgets[index]
            for position, widget in enumerate(widgets):
                widget["position"] = position
            try:
                self.dashboard = self.client.save_dashboard(self.dashboard)
            except ApiError as exc:
                self._set_status(exc.message, "error")
            self._render_shell()

    def hide_widget(self, index: int) -> None:
        widgets = self.dashboard.get("widgets", [])
        if 0 <= index < len(widgets):
            widgets[index]["hidden"] = True
            try:
                self.dashboard = self.client.save_dashboard(self.dashboard)
            except ApiError as exc:
                self._set_status(exc.message, "error")
            self._render_shell()

    def _data_lab(self) -> ft.Control:
        if not self.datasets:
            return ft.Column(
                [
                    title("Data Lab"),
                    ft.Container(height=18),
                    empty_state(
                        "No workbook yet",
                        "Upload an Excel workbook to unlock profiling, preview, and transformations.",
                        primary_button("Upload workbook", self.open_picker, ft.Icons.CLOUD_UPLOAD),
                    ),
                ]
            )
        dataset = self.active_dataset or self.datasets[0]
        current_profile = self.dataset_profiles.get(dataset["id"], {}) or dataset.get("profile", {})
        options = [
            ft.DropdownOption(key=item["id"], text=item["filename"]) for item in self.datasets
        ]
        picker = ft.Dropdown(
            value=dataset["id"],
            options=options,
            label="Active workbook",
            width=260 if self._compact_layout() else 310,
            on_select=lambda e: self.select_dataset(e.control.value),
        )
        columns = [
            item.get("name")
            for item in current_profile.get("column_profiles", [])
            if item.get("name")
        ]
        column_options = [ft.DropdownOption(key=value, text=value) for value in columns]
        filter_column = ft.Dropdown(
            options=column_options,
            label="Filter column",
            col={"xs": 12, "sm": 5},
        )
        filter_value = ft.TextField(
            label="Contains or equals",
            col={"xs": 12, "sm": 4},
        )
        operator = ft.Dropdown(
            value="contains",
            options=[
                ft.DropdownOption(key=k, text=t)
                for k, t in [
                    ("contains", "contains"),
                    ("eq", "equals"),
                    ("gt", "greater than"),
                    ("lt", "less than"),
                ]
            ],
            label="Operator",
            col={"xs": 12, "sm": 3},
        )
        return ft.Column(
            [
                self._screen_header(
                    "DATA LAB",
                    "Know the shape before the story.",
                    "Profile, preview, and make deliberate transformations without losing the original workbook.",
                    [
                        picker,
                        secondary_button(
                            "Export XLSX",
                            lambda _: self.export_dataset("xlsx"),
                            ft.Icons.DOWNLOAD,
                            disabled=self.busy,
                        ),
                    ],
                ),
                ft.Container(height=22),
                self._stat_grid(
                    [
                        stat_card(
                            ft.Icons.CHECK_CIRCLE,
                            "Quality score",
                            f"{self.active_dataset.get('quality_score', 0):.0f}%",
                            "Missingness + duplicates",
                            MINT,
                            MINT_LIGHT,
                        ),
                        stat_card(
                            ft.Icons.TABLE_VIEW,
                            "Rows",
                            f"{self.active_dataset.get('row_count', 0):,}",
                            "Rows in active sheet",
                            PURPLE,
                            PURPLE_LIGHT,
                        ),
                        stat_card(
                            ft.Icons.DATASET,
                            "Columns",
                            str(self.active_dataset.get("column_count", 0)),
                            "Detected fields",
                            BLUE,
                            BLUE_LIGHT,
                        ),
                        stat_card(
                            ft.Icons.WARNING_AMBER,
                            "Duplicate rows",
                            str(current_profile.get("duplicate_rows", 0)),
                            "Worth a closer look",
                            ORANGE,
                            ORANGE_LIGHT,
                        ),
                    ],
                ),
                ft.Container(height=18),
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            content=surface(
                                ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "Column health",
                                                size=16,
                                                color=INK,
                                                weight=ft.FontWeight.W_700,
                                            ),
                                            ft.Container(expand=True),
                                            label("Type / empty / unique", 11, MUTED),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    divider(),
                                    profile_rows(current_profile),
                                ],
                                spacing=12,
                            ),
                                padding=20,
                            ),
                            col={"xs": 12, "lg": 5},
                        ),
                        ft.Container(
                            content=surface(
                                ft.Column(
                                [
                                    ft.Text(
                                        "Quick transform",
                                        size=16,
                                        color=INK,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    label(
                                        "The source stays unchanged. Preview the result, then save it as a new analysis.",
                                        12,
                                        MUTED,
                                    ),
                                    ft.Container(height=8),
                                    ft.ResponsiveRow(
                                        [filter_column, operator, filter_value],
                                        spacing=10,
                                        run_spacing=10,
                                    ),
                                    ft.Row(
                                        [
                                            primary_button(
                                                "Apply filter",
                                                lambda _: self.apply_filter(
                                                    filter_column.value,
                                                    operator.value,
                                                    filter_value.value,
                                                ),
                                                ft.Icons.FILTER_ALT,
                                            ),
                                            secondary_button(
                                                "Drop empty rows",
                                                lambda _: self.drop_nulls(filter_column.value),
                                                ft.Icons.AUTO_AWESOME,
                                            ),
                                            *(
                                                [
                                                    secondary_button(
                                                        "Reset preview",
                                                        self.reset_preview,
                                                        ft.Icons.RESTART_ALT,
                                                    )
                                                ]
                                                if self.transformed
                                                else []
                                            ),
                                        ],
                                        wrap=True,
                                    ),
                                ],
                                spacing=12,
                            ),
                                padding=20,
                            ),
                            col={"xs": 12, "lg": 7},
                        ),
                    ],
                    spacing=14,
                    run_spacing=14,
                ),
                ft.Container(height=18),
                surface(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Workbook preview",
                                                size=16,
                                                color=INK,
                                                weight=ft.FontWeight.W_700,
                                            ),
                                            label(
                                                f"Showing the first {min(len(self.preview), 12)} rows",
                                                12,
                                                MUTED,
                                            ),
                                        ],
                                        spacing=3,
                                    ),
                                    ft.Container(expand=True),
                                    label(
                                        dataset.get("sheet_name", "Active sheet"),
                                        11,
                                        PURPLE,
                                        ft.FontWeight.W_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            divider(),
                            dataset_table(
                                self.transformed.get("preview", [])
                                if self.transformed
                                else self.preview,
                                compact=self.compact_tables,
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=20,
                ),
            ],
            spacing=0,
        )

    def select_dataset(self, dataset_id: str, refresh: bool = True) -> None:
        try:
            self.active_dataset = next(item for item in self.datasets if item["id"] == dataset_id)
            detail = self.client.dataset(dataset_id)
            self.active_dataset = detail["dataset"]
            self.dataset_profiles[dataset_id] = detail.get("profile", {})
            self.preview = detail.get("preview", [])
            self.transformed = None
            self.last_chart = None
            self.visual_draft = {}
        except (StopIteration, ApiError) as exc:
            self._set_status(str(exc), "error")
        if refresh:
            self._render_shell()

    def apply_filter(self, column: str | None, operator: str | None, value: str | None) -> None:
        if not self.active_dataset or not column or not value:
            self._set_status("Choose a column and value first.", "error")
            self._render_shell()
            return
        try:
            self.transformed = self.client.transform(
                self.active_dataset["id"],
                {
                    "operation": "filter",
                    "column": column,
                    "operator": operator or "contains",
                    "value": value,
                },
            )
        except ApiError as exc:
            self._set_status(exc.message, "error")
        else:
            self._set_status("Filter preview updated.", "success")
        self._render_shell()

    def drop_nulls(self, column: str | None) -> None:
        if not self.active_dataset:
            return
        try:
            self.transformed = self.client.transform(
                self.active_dataset["id"], {"operation": "drop_nulls", "column": column}
            )
        except ApiError as exc:
            self._set_status(exc.message, "error")
        else:
            self._set_status("Empty rows removed from the preview.", "success")
        self._render_shell()

    def reset_preview(self, _=None) -> None:
        self.transformed = None
        self._set_status("Preview reset to the original workbook.", "success")
        self._render_shell()

    @staticmethod
    def _is_numeric_column(profile: dict[str, Any]) -> bool:
        dtype = str(profile.get("dtype", "")).lower()
        return any(token in dtype for token in ("int", "float", "decimal", "uint", "duration"))

    def _set_visual_draft(self, key: str, value: str | None) -> None:
        if value:
            self.visual_draft[key] = value
        else:
            self.visual_draft.pop(key, None)
        self._render_shell()

    def _visuals(self) -> ft.Control:
        if not self.datasets:
            return ft.Column(
                [
                    title("Visuals"),
                    ft.Container(height=18),
                    empty_state(
                        "No dataset to visualize",
                        "Upload a workbook and your first chart can be ready in under a minute.",
                        primary_button("Upload workbook", self.open_picker, ft.Icons.CLOUD_UPLOAD),
                    ),
                ]
            )
        dataset = self.active_dataset or self.datasets[0]
        profile = self.dataset_profiles.get(dataset["id"], {}) or dataset.get("profile", {})
        column_profiles = profile.get("column_profiles", [])
        columns = [item.get("name") for item in column_profiles if item.get("name")]
        if not columns:
            columns = [str(column) for column in dataset.get("columns", []) if column]
        if len(columns) < 1:
            return empty_state(
                "This sheet has no usable columns",
                "Choose another sheet or upload a workbook with data.",
            )
        numeric_columns = [
            item["name"] for item in column_profiles if item.get("name") and self._is_numeric_column(item)
        ]
        dimension_columns = [column for column in columns if column not in numeric_columns]
        default_type = "bar" if numeric_columns else "pie"
        selected_type = self.visual_draft.get("chart_type", default_type)
        if selected_type == "histogram" and not numeric_columns:
            selected_type = "pie"
        x_options = numeric_columns if selected_type == "histogram" else columns
        x_default = self.visual_draft.get("x_column")
        if x_default not in x_options:
            x_default = (dimension_columns or x_options)[0]
        y_options = numeric_columns or columns
        y_default = self.visual_draft.get("y_column")
        if y_default not in y_options:
            y_default = y_options[0]
        is_count_chart = selected_type == "pie"
        aggregation_value = "count" if is_count_chart else self.visual_draft.get("aggregation", "sum")
        x = ft.Dropdown(
            value=x_default,
            options=[ft.DropdownOption(key=c, text=c) for c in x_options],
            label="Value to distribute" if selected_type == "histogram" else "Dimension / X axis",
            col={"xs": 12, "sm": 6, "lg": 4},
            on_select=lambda event: self._set_visual_draft("x_column", event.control.value),
        )
        y = ft.Dropdown(
            value=y_default,
            options=[ft.DropdownOption(key=c, text=c) for c in y_options],
            label="Measure / Y axis",
            col={"xs": 12, "sm": 6, "lg": 4},
            disabled=selected_type in {"histogram", "pie"},
            on_select=lambda event: self._set_visual_draft("y_column", event.control.value),
        )
        chart_type = ft.Dropdown(
            value=selected_type,
            options=[
                ft.DropdownOption(key=k, text=t)
                for k, t in [
                    ("bar", "Bar"),
                    ("line", "Line"),
                    ("scatter", "Scatter"),
                    ("histogram", "Histogram"),
                    ("pie", "Donut"),
                ]
                if k != "histogram" or numeric_columns
            ],
            label="Visual type",
            col={"xs": 12, "sm": 6, "lg": 2},
            on_select=lambda event: self._set_visual_draft("chart_type", event.control.value),
        )
        aggregation = ft.Dropdown(
            value=aggregation_value,
            options=[
                ft.DropdownOption(key=k, text=t)
                for k, t in [
                    ("sum", "Sum"),
                    ("mean", "Average"),
                    ("min", "Minimum"),
                    ("max", "Maximum"),
                    ("count", "Count"),
                ]
            ],
            label="Aggregation",
            col={"xs": 12, "sm": 6, "lg": 2},
            disabled=selected_type in {"histogram", "pie", "scatter"},
            on_select=lambda event: self._set_visual_draft("aggregation", event.control.value),
        )
        name = ft.TextField(
            value=(
                f"Distribution of {x_default}"
                if selected_type == "histogram"
                else f"{x_default} share"
                if selected_type == "pie"
                else f"{y_default} by {x_default}"
            ),
            label="Name this visual",
            col={"xs": 12, "lg": 12},
        )
        saved = self.visualizations[:4]
        chart_panel: ft.Control
        if self.last_chart:
            chart_panel = chart_card(
                self.last_chart.get("name", "New visual"),
                self.last_chart.get("spec", {}).get("chart", {}),
                f"Built from {dataset.get('filename', 'workbook')}",
            )
        elif saved:
            chart_panel = chart_card(
                saved[0].get("name", "Saved visual"),
                saved[0].get("spec", {}).get("chart", {}),
                "Most recently saved visual",
            )
        else:
            chart_panel = empty_state(
                "Your visual canvas is clear",
                "Choose the fields above and build a chart that answers one useful question.",
            )
        return ft.Column(
            [
                self._screen_header(
                    "VISUAL STUDIO",
                    "Make the signal visible.",
                    "Start with a question, then choose the smallest visual that makes the answer obvious.",
                    [
                        secondary_button(
                            "Data Lab",
                            lambda _: self.navigate("Data Lab"),
                            ft.Icons.DATA_EXPLORATION,
                        ),
                    ],
                ),
                ft.Container(height=22),
                surface(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        "Chart builder",
                                        size=16,
                                        color=INK,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    ft.Container(expand=True),
                                    label(
                                        dataset.get("filename", "Active workbook"),
                                        11,
                                        PURPLE,
                                        ft.FontWeight.W_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            label("The canvas updates when you save a visual.", 12, MUTED),
                            ft.Container(height=10),
                            ft.ResponsiveRow(
                                [name, chart_type, x, y, aggregation],
                                spacing=10,
                                run_spacing=10,
                            ),
                            ft.Container(height=8),
                            primary_button(
                                "Build and save visual",
                                lambda _: self.build_chart(
                                    name.value,
                                    chart_type.value,
                                    x.value,
                                    y.value,
                                    aggregation.value,
                                ),
                                ft.Icons.AUTO_AWESOME,
                                disabled=self.busy,
                            ),
                        ],
                        spacing=12,
                    ),
                    padding=20,
                ),
                ft.Container(height=18),
                chart_panel,
            ],
            spacing=0,
        )

    def build_chart(self, name: str, chart_type: str, x: str, y: str, aggregation: str) -> None:
        if not self.active_dataset:
            return
        profile = self.dataset_profiles.get(self.active_dataset["id"], {})
        numeric_columns = {
            item.get("name")
            for item in profile.get("column_profiles", [])
            if item.get("name") and self._is_numeric_column(item)
        }
        if chart_type == "histogram" and x not in numeric_columns:
            self._set_status("Choose a numeric field for a histogram.", "error")
            self._render_shell()
            return
        if chart_type in {"bar", "line", "scatter"} and aggregation != "count" and y not in numeric_columns:
            self._set_status("Choose a numeric measure, or use Count to compare categories.", "error")
            self._render_shell()
            return
        try:
            self.last_chart = self.client.create_chart(
                self.active_dataset["id"],
                {
                    "name": name or "Untitled insight",
                    "chart_type": chart_type or "bar",
                    "x_column": x,
                    "y_column": y,
                    "aggregation": aggregation or "sum",
                },
            )
            self.visualizations.insert(0, self.last_chart)
            widget_id = f"chart-{self.last_chart['id']}"
            widgets = self.dashboard.setdefault("widgets", [])
            if not any(widget.get("id") == widget_id for widget in widgets):
                widgets.append(
                    {
                        "id": widget_id,
                        "kind": "chart",
                        "title": name or "Untitled insight",
                        "subtitle": f"{chart_type.title()} visual from {self.active_dataset.get('filename', 'workbook')}",
                        "color": PURPLE,
                        "visualization_id": self.last_chart["id"],
                        "position": len(widgets),
                    }
                )
                self.dashboard = self.client.save_dashboard(self.dashboard)
            self._set_status("Visual saved to your workspace.", "success")
        except ApiError as exc:
            self._set_status(exc.message, "error")
        self._render_shell()

    def _settings(self) -> ft.Control:
        user = self.client.user or {}
        profile_card = surface(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.PERSON_OUTLINE, PURPLE, PURPLE_LIGHT),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Profile", size=16, color=INK, weight=ft.FontWeight.W_700
                                    ),
                                    label("How InsightForge greets you", 12, MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    divider(),
                    label("FULL NAME", 10, MUTED, ft.FontWeight.W_700),
                    ft.Text(user.get("full_name", "Explorer"), size=16, color=INK),
                    label("EMAIL", 10, MUTED, ft.FontWeight.W_700),
                    ft.Text(user.get("email", ""), size=16, color=INK),
                ],
                spacing=12,
            ),
            padding=20,
        )
        appearance_card = surface(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.DARK_MODE, BLUE, BLUE_LIGHT),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Appearance", size=16, color=INK, weight=ft.FontWeight.W_700
                                    ),
                                    label("A focused canvas for long analysis sessions", 12, MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    divider(),
                    ft.Switch(
                        label="Use dark canvas",
                        value=self.page.theme_mode == ft.ThemeMode.DARK,
                        on_change=self.toggle_dark_mode,
                    ),
                    ft.Switch(
                        label="Compact data tables",
                        value=self.compact_tables,
                        on_change=self.toggle_compact_tables,
                    ),
                    ft.Switch(
                        label="Show insight suggestions",
                        value=self.show_suggestions,
                        on_change=self.toggle_suggestions,
                    ),
                ],
                spacing=12,
            ),
            padding=20,
        )
        privacy_card = surface(
            ft.Column(
                [
                    ft.Row(
                        [
                            icon_box(ft.Icons.LOCK_RESET, MINT, MINT_LIGHT),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Trust and privacy",
                                        size=16,
                                        color=INK,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    label("Your workbooks stay scoped to your account", 12, MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    divider(),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=MINT, size=18),
                            label("Private by default", 13, INK),
                            ft.Container(expand=True),
                            label("Local storage + per-user authorization", 12, MUTED),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=MINT, size=18),
                            label("Exportable anytime", 13, INK),
                            ft.Container(expand=True),
                            label("CSV or Excel", 12, MUTED),
                        ]
                    ),
                ],
                spacing=14,
            ),
            padding=20,
        )
        hidden_count = sum(1 for item in self.dashboard.get("widgets", []) if item.get("hidden"))
        dashboard_card = surface(
            ft.Row(
                [
                    icon_box(ft.Icons.DASHBOARD_CUSTOMIZE, ORANGE, ORANGE_LIGHT),
                    ft.Column(
                        [
                            ft.Text(
                                "Dashboard layout",
                                size=16,
                                color=INK,
                                weight=ft.FontWeight.W_700,
                            ),
                            label(
                                f"{hidden_count} hidden card{'s' if hidden_count != 1 else ''}",
                                12,
                                MUTED,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    secondary_button(
                        "Restore hidden cards",
                        self.restore_hidden_widgets,
                        ft.Icons.UNDO,
                    )
                    if hidden_count
                    else label("Everything is visible", 12, MINT),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
        )
        return ft.Column(
            [
                self._screen_header(
                    "WORKSPACE SETTINGS",
                    "Shape the way clarity feels.",
                    "Make the workspace yours without making the data harder to trust.",
                    [
                        secondary_button(
                            "Back to overview",
                            lambda _: self.navigate("Overview"),
                            ft.Icons.DASHBOARD,
                        ),
                    ],
                ),
                ft.Container(height=22),
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            content=profile_card,
                            col={"xs": 12, "lg": 5},
                        ),
                        ft.Container(
                            content=appearance_card,
                            col={"xs": 12, "lg": 7},
                        ),
                    ],
                    spacing=14,
                    run_spacing=14,
                ),
                ft.Container(height=18),
                privacy_card,
                ft.Container(height=14),
                dashboard_card,
            ],
            spacing=0,
        )

    def toggle_dark_mode(self, event: ft.ControlEvent) -> None:
        self.page.theme_mode = ft.ThemeMode.DARK if event.control.value else ft.ThemeMode.LIGHT
        self.page.update()

    def toggle_compact_tables(self, event: ft.ControlEvent) -> None:
        self.compact_tables = bool(event.control.value)
        self._render_shell()

    def toggle_suggestions(self, event: ft.ControlEvent) -> None:
        self.show_suggestions = bool(event.control.value)
        self._render_shell()

    async def open_picker(self, _=None) -> None:
        if self.busy:
            return
        try:
            files = await self.file_picker.pick_files(
                dialog_title="Choose an Excel workbook",
                allow_multiple=False,
                with_data=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx", "xlsm", "xls"],
            )
            if not files:
                return
            selected = files[0]
            content = selected.bytes
            if content is None and selected.path:
                content = Path(selected.path).read_bytes()
            if not content:
                raise ApiError("The selected workbook could not be read.")
            self.busy = True
            self._set_status(f"Uploading {selected.name}…", "info")
            self._render_shell()
            result = await asyncio.to_thread(self.client.upload, selected.name, content)
            self.datasets.insert(0, result["dataset"])
            self.active_dataset = result["dataset"]
            self.dataset_profiles[result["dataset"]["id"]] = result.get("profile", {})
            self.preview = result.get("preview", [])
            self.dashboard = await asyncio.to_thread(self.client.dashboard)
            self._set_status(f"{selected.name} is ready to explore.", "success")
            self.current_view = "Data Lab"
        except ApiError as exc:
            self._set_status(exc.message, "error")
        except OSError as exc:
            self._set_status(f"The workbook could not be read: {exc}", "error")
        finally:
            self.busy = False
            self._render_shell()

    async def export_dataset(self, file_format: str = "xlsx") -> None:
        if not self.active_dataset or self.busy:
            return
        try:
            self.busy = True
            self._set_status("Preparing your export…", "info")
            self._render_shell()
            name, content = await asyncio.to_thread(
                self.client.export, self.active_dataset["id"], file_format
            )
            await self.save_picker.save_file(
                dialog_title="Save your export", file_name=name, src_bytes=content
            )
            self._set_status("Export ready.", "success")
        except ApiError as exc:
            self._set_status(exc.message, "error")
        finally:
            self.busy = False
            self._render_shell()


def run_app() -> None:
    ft.run(main, assets_dir="assets")


def main(page: ft.Page) -> None:
    InsightForgeApp(page)


if __name__ == "__main__":
    run_app()
