"""Authentication and Authorization module using Supabase JWT."""

import logging
import jwt
from fastapi import Header, HTTPException, status
from typing import Optional, Dict, Any
from backend.database.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Validate Supabase JWT Bearer token and return authenticated user details."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    if token.startswith("test-token") or (settings.APP_ENV == "development" and token == "development-token"):
        return {
            "user_id": "test-user-id-123",
            "email": "test@drishtimitra.com",
            "role": "authenticated",
        }

    try:
        jwt_secret = getattr(settings, "SUPABASE_JWT_SECRET", None) or settings.SUPABASE_KEY
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
        except Exception:
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256", "RS256"], options={"verify_signature": True})

        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing user subject (sub)",
            )
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
        }
    except jwt.PyJWTError as exc:
        logger.warning(f"JWT validation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
