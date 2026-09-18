from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Transaction
from app.models.account import Account
from app.models.user import User
from app.security.auth import get_current_user
from app.schemas.accounts import AccountResponse, DepositRequest
from app.utils.transaction_reference import generate_transaction_reference

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)

@router.get("/me", response_model=AccountResponse)
def get_my_account(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    account = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .first()
    )
    return account

@router.get("/lookup/{account_number}", response_model=AccountResponse)
def lookup_account(
        account_number: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    account = (
        db.query(Account)
        .filter(Account.account_number == account_number)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )
    return account

@router.post("/me/deposit")
def deposit(
        data: DepositRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    account = (db.query(Account).filter(Account.user_id == current_user.id).first())
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    try:
        account.balance += data.amount

        transaction = Transaction(
            reference=generate_transaction_reference(),
            amount=data.amount,
            transaction_type="DEPOSIT",
            account_id=account.id
        )

        db.add(transaction)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(account)
    db.refresh(transaction)

    return {
        "message": "Deposit Successful",
        "account_number": account.account_number,
        "amount": transaction.amount,
        "balance": account.balance,
        "reference": transaction.reference
    }




