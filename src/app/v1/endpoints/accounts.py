import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.account_model import Account, AccountType
from app.models.users_model import User
from app.schemas.account_schema import AccountCreateSchema, AccountLookupResponse, AccountResponseSchema
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

@router.get("/lookup/{account_number}", response_model=AccountLookupResponse)
async def lookup_account_by_number(
    account_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """check for a beneficiary account by full account number to verify recipient name."""
    stmt = (
        select(Account, User)
        .join(User, Account.user_id == User.id)
        .where(Account.account_number == account_number)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account number not found."
        )

    account, owner = row

    if account.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is your own account. Use internal transfers instead."
        )

    masked_acc = f"****{account.account_number[-4:]}" if len(account.account_number) >= 4 else account.account_number

    return {
        "account_id": str(account.id),
        "account_number_masked": masked_acc,
        "account_type": account.account_type,
        "owner_name": owner.full_name
    }
