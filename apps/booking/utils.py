from .exceptions import MissingIdempotencyKeyError

def require_idempotency_key(request) -> str:
    key = request.headers.get("Idempotency-Key")
    if not key:
        raise MissingIdempotencyKeyError()
    return key