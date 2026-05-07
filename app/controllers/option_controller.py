from fastapi import APIRouter, HTTPException

from decimal import Decimal

from datetime import datetime

from app.models.option import (
    Option,
    OptionType
)

from app.repositories.option_repository import (
    OptionRepository
)

router = APIRouter(
    prefix="/market/options"
)

option_repo = OptionRepository()


@router.get("/")
def get_options():

    options = option_repo.find_all_active()

    return [
        {
            "option_id": o.option_id,
            "underlying_ticker": o.underlying_ticker,
            "option_type": o.option_type.value,
            "strike_price": str(o.strike_price),
            "expiry_time": o.expiry_time.isoformat(),
            "premium": str(o.premium),
            "is_active": o.is_active
        }
        for o in options
    ]

@router.get("/{option_id}")
def get_option(option_id: str):

    option = option_repo.find_by_id(
        option_id
    )

    if not option:

        raise HTTPException(
            status_code=404,
            detail="Option not found"
        )

    return {
        "option_id": option.option_id,
        "underlying_ticker":
            option.underlying_ticker,
        "option_type":
            option.option_type.value,
        "strike_price":
            str(option.strike_price),
        "expiry_time":
            option.expiry_time.isoformat(),
        "premium":
            str(option.premium),
        "is_active":
            option.is_active
    }
