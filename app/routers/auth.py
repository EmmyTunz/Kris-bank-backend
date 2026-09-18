from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.security.auth import get_current_user
from app.models.account import Account
from app.utils.account_number import generate_account_number



router = APIRouter(
    prefix='/auth',
    tags=["Authentication"]
)

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone_number=data.phone_number,
        password_hash=hash_password(data.password)
    )
    try:
        db.add(user)
        db.flush()

        account = Account(
            account_number=generate_account_number(db),
            balance=0,
            user_id=user.id
        )

        db.add(account)
        db.commit()
        db.refresh(user)
        db.refresh(account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email or phone number already registered"
        )

    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "email": user.email,
        "account_number": account.account_number
    }

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone_number": current_user.phone_number
    }