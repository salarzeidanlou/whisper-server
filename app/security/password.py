import bcrypt

# Generated once at process startup and used when a username does not exist.
DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt(rounds=12)).decode("ascii")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (TypeError, ValueError, UnicodeError):
        return False
