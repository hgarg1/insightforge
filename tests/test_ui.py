import flet as ft

from insightforge.ui.app import InsightForgeApp
from insightforge.ui.components import chart_control


class Session:
    pass


def test_auth_shell_and_chart_controls_construct():
    page = ft.Page(Session())
    page.update = lambda *controls: None
    app = InsightForgeApp(page)
    assert len(page.controls) == 1
    assert len(page.overlay) == 0
    assert len(page.services) == 2
    assert all(isinstance(service, ft.FilePicker) for service in page.services)

    app.auth.viewport_width = 770
    compact_auth_shell = app.auth.render()
    assert app.auth.email.width == app.auth._auth_form_width() == 430
    assert app.auth.password.width == app.auth.email.width
    compact_auth_scroller = compact_auth_shell.content.controls[1].content
    assert compact_auth_scroller.scroll == ft.ScrollMode.ALWAYS
    assert compact_auth_scroller.expand is True

    app.auth.viewport_width = 375
    app.auth.render()
    assert app.auth.email.width == app.auth._auth_form_width() == 299

    # Every potentially tall auth state uses the same locally scrolling pane.
    app.auth.viewport_width = 1280
    for mode in ("login", "signup", "reset-request", "reset-confirm"):
        app.auth.mode = mode
        auth_shell = app.auth.render()
        auth_scroller = auth_shell.content.controls[1].content
        assert auth_scroller.scroll == ft.ScrollMode.ALWAYS
        assert auth_scroller.expand is True

    # Login does not mount the password checklist; typing must not update a
    # detached control and crash the live Flet session.
    app.auth.mode = "login"
    app.auth._update_password_checklist()

    app.client.user = {"full_name": "Test Explorer", "email": "test@example.com", "plan": "Creator"}
    app.datasets = [
        {
            "id": "dataset-1",
            "filename": "sales.xlsx",
            "quality_score": 96.0,
            "row_count": 3,
            "column_count": 3,
            "sheet_name": "Sales",
        }
    ]
    app.active_dataset = app.datasets[0]
    app.dashboard = {"name": "My command center", "widgets": []}
    app._render_shell()
    workspace_content = app._content()
    assert workspace_content.content.scroll == ft.ScrollMode.AUTO
    assert workspace_content.content.expand is True
    app._responsive_width = 390
    assert app._layout_mode() == "mobile"
    assert len(app._bottom_nav().content.controls) == 4
    assert chart_control({"chart_type": "histogram", "x": [1, 2, 3], "y": [1, 1, 1]})
