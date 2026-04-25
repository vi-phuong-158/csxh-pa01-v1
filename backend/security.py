from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from backend.config import settings

_signer = TimestampSigner(settings.SECRET_KEY, salt="session")


def create_session_token(user_id: int) -> str:
    return _signer.sign(str(user_id)).decode()


def verify_session_token(token: str) -> int | None:
    try:
        value = _signer.unsign(token, max_age=settings.SESSION_MAX_AGE)
        return int(value.decode())
    except (BadSignature, SignatureExpired, ValueError):
        return None
