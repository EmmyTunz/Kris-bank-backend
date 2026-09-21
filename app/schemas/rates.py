from decimal import Decimal
from pydantic import BaseModel

class RatesResponse(BaseModel):
    base_currency: str
    rates: dict[str, Decimal]
