from threading import activeCount

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc

from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Transaction
from app.models.account import Account
from app.models.user import User
from app.security.auth import get_current_user
from app.schemas.accounts import *
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

@router.post("/me/withdraw")
def withdraw(
        data: WithdrawalRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    account = (db.query(Account).filter(Account.user_id == current_user.id).first())
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    if account.balance < data.amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance"
        )

    try:
        account.balance -= data.amount

        transaction = Transaction(
            reference=generate_transaction_reference(),
            amount=data.amount,
            transaction_type="WITHDRAWAL",
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
        "message": "Withdrawal successful",
        "account_number": account.account_number,
        "amount": transaction.amount,
        "balance": account.balance,
        "reference": transaction.reference
    }

@router.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    account = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(desc(Transaction.created_at))
        .all()
    )

    return transactions

@router.get("/transaction/{reference}", response_model=TransactionResponse)
def get_transaction(
        reference: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    account = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    transaction = (
        db.query(Transaction)
        .filter(Transaction.reference == reference,
                Transaction.account_id == account.id
        )
        .first()
    )
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )
    return transaction

#transfer to another user
@router.post("/transfers")
def transfer(
        data: TransferRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    sender = (
        db.query(Account)
        .filter(Account.user_id == current_user.id)
        .first()
    )
    if not sender:
        raise HTTPException(
            status_code=404,
            detail="You don't have an account"
        )

    # get receiver details
    receiver = (
        db.query(Account)
        .filter(Account.account_number == data.account_number)
        .first()
    )

    if not receiver:
        raise HTTPException(
            status_code=404,
            detail="Receiver account not found"
        )

    receiver_user = (
        db.query(User)
        .filter(User.id == receiver.user_id)
        .first()
    )

    if not receiver_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if sender.id == receiver.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot transfer to self"
        )
    if sender.balance < data.amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient Funds"
        )

    # Lock query -- to prevent concurrent transactions
    locked_accounts = (
        db.query(Account)
        .filter(
            Account.id.in_([sender.id, receiver.id])
        )
        .with_for_update()
        .all()
    )

    accounts = {
        account.id: account
        for account in locked_accounts
    }
    sender = accounts[sender.id]
    receiver = accounts[receiver.id]

    # Send Money
    try:
        if sender.balance < data.amount:
            raise HTTPException(
                status_code=400,
                detail="Insufficient Funds"
            )
        sender.balance -= data.amount
        receiver.balance += data.amount

        # save trans record for sender
        sender_transaction = Transaction(
            reference=generate_transaction_reference(),
            amount=data.amount,
            transaction_type="TRANSFER_OUT",
            account_id=sender.id
        )

        # save trans record for receiver
        receiver_transaction = Transaction(
            reference=generate_transaction_reference(),
            amount=data.amount,
            transaction_type="TRANSFER_IN",
            account_id=receiver.id
        )

        db.add(sender_transaction)
        db.add(receiver_transaction)
        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(sender)
    db.refresh(receiver)

    return {
        "message": "Transfer Successful",
        "from_account": sender.account_number,
        "to_account": receiver.account_number,
        "receiver_name": f"{receiver_user.first_name} {receiver_user.last_name}",
        "amount": data.amount,
        "sender_balance": sender.balance,
        "sender_reference": sender_transaction.reference,
    }