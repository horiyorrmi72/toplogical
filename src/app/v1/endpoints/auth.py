import random
from decimal import Decimal
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config_core import settings
from app.core.security_core import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.account_model import Account, AccountType
from app.models.notifications_model import Notification
from app.models.users_model import User
from app.schemas.auth_schema import (
    LoginSchema,
    TokenSchema,
    UserRegisterSchema,
    UserResponseSchema,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = UUID(sub)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


@router.post(
    "/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserRegisterSchema, db: AsyncSession = Depends(get_db)):
    existing = (
        await db.execute(select(User).where(User.email == user_in.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, detail="User with this email already exists."
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    await db.flush()

    acc_num = "".join([str(random.randint(0, 9)) for _ in range(10)])
    accounts_to_create = [
        (AccountType.CHECKING, Decimal("1000.00"), Decimal("0.00")),
        (AccountType.SAVINGS, Decimal("500.00"), Decimal("0.00")),
        (AccountType.CREDIT_CARD, Decimal("0.00"), Decimal("5000.00")),
    ]
    for account_type, initial_balance, credit_limit in accounts_to_create:
        acc_num = "".join([str(random.randint(0, 9)) for _ in range(10)])
        account = Account(
            user_id=user.id,
            account_number=acc_num,
            account_type=account_type,
            balance=initial_balance,
            credit_limit=credit_limit,
        )
        db.add(account)

    welcome_notif = Notification(
        user_id=user.id,
        title="Welcome to FinBank!",
        message="Your Checking, Savings, and Credit Card accounts have been successfully created.Enjoy Banking!",
    )
    db.add(welcome_notif)

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenSchema)
@limiter.limit("5/minute")
async def login(
    request: Request, login_data: LoginSchema, db: AsyncSession = Depends(get_db)
):
    user = (
        await db.execute(select(User).where(User.email == login_data.email))
    ).scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(subject=str(user.id))

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponseSchema)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
