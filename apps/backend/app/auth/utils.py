"""Authentication utility functions."""

import secrets
import string


def generate_verification_token(length: int = 32) -> str:
    """Generate a secure random token for email verification or password reset."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key(length: int = 32) -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(length)