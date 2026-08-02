from slowapi import Limiter
from jose import jwt, JWTError
from starlette.requests import Request
from app.core.config import settings

def get_user_id_or_ip(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return f"user:{payload.get('sub')}"
        except JWTError:
            pass
    return f"ip:{request.client.host}"

limiter = Limiter(
    key_func=get_user_id_or_ip,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
)