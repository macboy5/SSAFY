import hashlib
import secrets

_LEGACY_ITERATIONS = 200_000
_ITERATIONS = 600_000
_ALGORITHM = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        parts = password_hash.split("$")
        if len(parts) == 4 and parts[0] == _ALGORITHM:
            _, iterations_text, salt, digest_hex = parts
            iterations = int(iterations_text)
        elif len(parts) == 2:
            # Community passwords created before account support used this format.
            salt, digest_hex = parts
            iterations = _LEGACY_ITERATIONS
        else:
            return False
        if iterations < 1 or iterations > 2_000_000:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), iterations
        )
    except (TypeError, ValueError):
        return False
    return secrets.compare_digest(digest.hex(), digest_hex)


def create_session_token() -> str:
    """Return a high-entropy opaque token suitable for a Bearer credential."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """One-way digest used as the auth_sessions lookup key."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
