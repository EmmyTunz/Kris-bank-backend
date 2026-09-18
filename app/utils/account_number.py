import random

from sqlalchemy.orm import Session
from app.models.account import Account

def generate_account_number(db: Session):
    while True:
        account_number = str(random.randint(1000000000, 9999999999))
        existing_account = (
            db.query(Account)
            .filter(Account.account_number == account_number)
            .first()
        )
        if not existing_account:
            return account_number

