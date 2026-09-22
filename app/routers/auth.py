from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, ChangePinRequest, ChangePasswordRequest, \
    UpdateProfileRequest, RefreshTokenRequest
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token, hash_refresh_token
from app.security.auth import get_current_user
from app.models.account import Account
from app.utils.account_number import generate_account_number
from app.security.pin import hash_pin, verify_pin
from app.models.refresh_token import RefreshToken

import jwt
from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY




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
    refresh_token_login = create_refresh_token(user.id)

    refresh_token_record = RefreshToken(
        token_hash=hash_refresh_token(refresh_token_login),
        user_id = user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )

    db.add(refresh_token_record)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_login,
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

@router.post("/me/change-pin")
def change_pin(
        data: ChangePinRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.pin_hash is not None:
        if data.current_pin is None:
            raise HTTPException(
                status_code=400,
                detail="Current PIN is required"
            )
        if not verify_pin(data.current_pin, current_user.pin_hash):
            raise HTTPException(
                status_code=400,
                detail="Current PIN is incorrect"
            )

    current_user.pin_hash = hash_pin(data.new_pin)
    db.commit()
    return {
        "message": "PIN set successfully"
    }

@router.post("/me/change-password")
def change_password(
        data: ChangePasswordRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # verify old password
    if not verify_password(
        data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Wrong Password"
        )

    # change password
    current_user.password_hash = hash_password(data.new_password)
    db.commit()

    return {
        "message": "Password changed Successfully"
    }

@router.patch("")
def change_profile(
        data: UpdateProfileRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # update only fields that are actually provided
    if data.first_name is not None:
        current_user.first_name = data.first_name
    if data.last_name is not None:
        current_user.last_name = data.last_name
    if data.phone_number is not None:
        current_user.phone_number = data.phone_number

    # protect the uniqueness of the user's phone number
    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered"
        )

    return {
        "message": "Profile updated successfully",
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone_number": current_user.phone_number
    }

# user log out
@router.post("/logout")
def logout():
    return {
        "message": "Logged out successfully"
    }

@router.post("/refresh")
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    # get refresh_token from db
    token_hash = hash_refresh_token(data.refresh_token)

    refresh_token_record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    # check db for hashed refresh token
    if not refresh_token_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    # is revoked?
    if refresh_token_record.revoked:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has been revoked"
        )

    # is expired?
    if refresh_token_record.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired"
        )

    # get user_id
    user_id = refresh_token_record.user_id

    access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    # revoke old refresh token
    refresh_token_record.revoked = True

    # store new refresh token
    new_refresh_token_record = RefreshToken(
        token_hash=hash_refresh_token(new_refresh_token),
        user_id=user_id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    )

    db.add(new_refresh_token_record)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to refresh token"
        )

    # try:
    #     payload = jwt.decode(
    #         data.refresh_token,
    #         JWT_SECRET_KEY,
    #         algorithms=[JWT_ALGORITHM]
    #     )
    # except jwt.InvalidTokenError:
    #     raise HTTPException(
    #         status_code=401,
    #         detail="Invalid or expired refresh token"
    #     )
    #
    # # check for refresh token
    # token_type = payload.get("type")
    # if token_type != "refresh":
    #     raise HTTPException(
    #         status_code=401,
    #         detail="Invalid refresh token"
    #     )
    #
    # # get user id, then create new access token
    # user_id = payload.get("sub")
    #
    # if not user_id:
    #     raise HTTPException(
    #         status_code= 401,
    #         detail="Invalid refresh token"
    #     )
    #
    # # create new access token
    # access_token = create_access_token(int(user_id))

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }