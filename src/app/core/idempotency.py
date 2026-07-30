from typing import Optional

from fastapi import Header, HTTPException, status

# in-memory cache for idempotency tokens we'd use redis for this in production.
PROCESSED_KEYS: set[str] = set()


async def verify_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
):
    """Ensures transfer requests with the same key are executed exactly once."""
    if not idempotency_key:
        return None
    if idempotency_key in PROCESSED_KEYS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate transaction request detected. This request has already been processed.",
        )

    PROCESSED_KEYS.add(idempotency_key)
    return idempotency_key
