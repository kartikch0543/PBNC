import pytest
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing():
    password = "supersecretpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_generation_and_decoding():
    user_id = "11111111-2222-3333-4444-555555555555"
    token = create_access_token(subject=user_id, extra_claims={"email": "test@example.com"})
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["email"] == "test@example.com"
    assert "exp" in payload
    assert "iat" in payload
