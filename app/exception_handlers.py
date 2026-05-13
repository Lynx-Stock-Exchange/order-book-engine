from fastapi import Request
from fastapi.responses import JSONResponse

from app.errors import OrderRejected


async def order_rejected_handler(
    request: Request,
    exc: OrderRejected
):

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": {}
            }
        }
    )