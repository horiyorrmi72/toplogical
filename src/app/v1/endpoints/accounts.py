import random

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.account_model import Account, AccountType
from app.models.users_model import User
from app.schemas.account_schema import AccountCreateSchema, AccountResponseSchema
from app.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=list[AccountResponseSchema])
async def list_user_accounts(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Fetch all accounts belonging to the authenticated user."""
    result = await db.execute(select(Account).where(Account.user_id == current_user.id))
    return result.scalars().all()


@router.post(
    "/", response_model=AccountResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_account(
    data: AccountCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new Checking, Savings, or Credit Card account."""
    acc_num = "".join([str(random.randint(0, 9)) for _ in range(10)])
    credit_limit = 3000.00 if data.account_type == AccountType.CREDIT_CARD else 0.00

    account = Account(
        user_id=current_user.id,
        account_number=acc_num,
        account_type=data.account_type,
        balance=data.initial_deposit,
        credit_limit=credit_limit,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account
