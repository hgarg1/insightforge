import httpx

from insightforge.ui.client import _response_error


def _response(status_code: int, payload: object) -> httpx.Response:
    request = httpx.Request("POST", "http://example.test/api/auth/signup")
    return httpx.Response(status_code, json=payload, request=request)


def test_api_errors_are_humanized_before_reaching_the_ui():
    response = _response(
        422,
        {
            "detail": [
                {"loc": ["body", "email"], "msg": "value is not a valid email address"},
                {"loc": ["body", "password"], "msg": "String should have at least 12 characters"},
            ]
        },
    )

    assert _response_error(response) == (
        "Email: value is not a valid email address "
        "Password: String should have at least 12 characters"
    )


def test_json_encoded_download_error_is_not_displayed_as_json():
    request = httpx.Request("GET", "http://example.test/api/datasets/1/export")
    response = httpx.Response(404, text='{"detail":"Dataset not found"}', request=request)

    assert _response_error(response) == "Dataset not found"
