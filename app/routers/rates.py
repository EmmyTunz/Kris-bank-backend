from fastapi import APIRouter

from app.schemas.rates import RatesResponse
from app.models.rates import Rate
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter
from app.database.session import get_db


router = APIRouter(
    prefix="/rates",
    tags=["Rates"]
)

@router.get("", response_model=RatesResponse)
def get_rates(
        db: Session = Depends(get_db)
):
    rates = db.query(Rate).all()

    return {
        "base_currency": "NGN",
        "rates": {
            rate.target_currency: rate.rate
            for rate in rates
        }
    }