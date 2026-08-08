from insightforge.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_token,
    password_requirements,
    verify_password,
)


def test_password_hash_and_access_token_round_trip():
    encoded = hash_password("correct horse battery staple")
    assert encoded != "correct horse battery staple"
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)

    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"


def test_password_complexity_policy():
    assert password_requirements("CorrectHorse!42") == ()
    assert password_requirements("short") == (
        "12 or more characters",
        "an uppercase letter",
        "a number",
        "a symbol",
    )
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("def")
