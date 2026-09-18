from decimal import Decimal
from pydantic import BaseModel, Field

import datetime

class AccountResponse(BaseModel):
    account_number: str
    balance: Decimal

class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)

class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(gt=0)

class TransactionResponse(BaseModel):
    reference: str
    amount: Decimal
    transaction_type: str
    created_at: datetime