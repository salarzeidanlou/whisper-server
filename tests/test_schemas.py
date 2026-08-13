import base64

import pytest

from app.schemas.auth import RegisterRequest


def _public_key() -> str:
    return base64.b64encode(b"k" * 32).decode("ascii")


def test_registration_normalizes_username() -> None:
    request = RegisterRequest(
        username="Alice_123",
        password="a-secure-password",
        public_key=_public_key(),
    )

    assert request.username == "alice_123"


@pytest.mark.parametrize("public_key", ["", "not-base64", base64.b64encode(b"short").decode()])
def test_registration_rejects_invalid_public_keys(public_key: str) -> None:
    with pytest.raises(ValueError):
        RegisterRequest(
            username="alice",
            password="a-secure-password",
            public_key=public_key,
        )


def test_registration_rejects_passwords_over_bcrypt_limit() -> None:
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        RegisterRequest(
            username="alice",
            password="é" * 37,
            public_key=_public_key(),
        )
