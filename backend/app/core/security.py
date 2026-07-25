from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create a secure hash for a plain-text password."""

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check whether a password matches a stored hash."""

    return password_hash.verify(
        plain_password,
        hashed_password,
    )