from decimal import Decimal
from pydantic import BaseModel, Field

class AccountResponse(BaseModel):
    account_number: str
    balance: Decimal

class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)

