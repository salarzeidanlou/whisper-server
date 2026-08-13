import pytest

from app.config import Settings, _is_unsafe_secret


@pytest.mark.parametrize(
    "secret",
    [
        "",
        "secret",
        "short",
        "CHANGE-ME-IN-PRODUCTION",
        "CHANGE-ME-generate-a-64-char-hex-secret",
    ],
)
def test_rejects_unsafe_jwt_secrets(secret: str) -> None:
    assert _is_unsafe_secret(secret)


def test_accepts_strong_jwt_secret() -> None:
    assert not _is_unsafe_secret("a" * 64)


def test_settings_reject_invalid_ticket_ttl() -> None:
    with pytest.raises(ValueError):
        Settings(WS_TICKET_TTL=0)
