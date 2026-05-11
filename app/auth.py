import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

internal_key_header = APIKeyHeader(name="X-Internal-Token", auto_error=False)
admin_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)
platform_id_header = APIKeyHeader(name="X-Platform-ID", auto_error=False)


def verify_internal_token(
    x_internal_token: str = Security(internal_key_header),
):
    expected = os.getenv("INTERNAL_API_KEY", "")
    if not expected or x_internal_token != expected:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "PLATFORM_NOT_AUTHORIZED",
                    "message": "Invalid or missing internal token",
                }
            },
        )


def get_platform_id(
    x_internal_token: str = Security(internal_key_header),
    x_platform_id: str = Security(platform_id_header),
) -> str:
    expected = os.getenv("INTERNAL_API_KEY", "")
    if not expected or x_internal_token != expected:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "PLATFORM_NOT_AUTHORIZED",
                    "message": "Invalid or missing internal token",
                }
            },
        )
    if not x_platform_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "PLATFORM_NOT_AUTHORIZED",
                    "message": "Missing X-Platform-ID header",
                }
            },
        )
    return x_platform_id


def verify_admin_token(
    x_admin_token: str = Security(admin_key_header),
):
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected or x_admin_token != expected:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "PLATFORM_NOT_AUTHORIZED",
                    "message": "Invalid or missing admin token",
                }
            },
        )
