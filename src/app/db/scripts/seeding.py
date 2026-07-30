import asyncio
from decimal import Decimal

from app.core.security_core import get_password_hash
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.account_model import Account, AccountType
from app.models.notifications_model import Notification
from app.models.transactions_model import (
    Transaction,
    TransactionCategory,
    TransactionStatus,
)
from app.models.users_model import User


async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # mock User
        user = User(
            email="john@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="John Smith",
        )
        db.add(user)
        await db.flush()

        # create Accounts matching spec
        checking = Account(
            user_id=user.id,
            account_number="9876544829",
            account_type=AccountType.CHECKING,
            balance=Decimal("4520.50"),
        )
        savings = Account(
            user_id=user.id,
            account_number="9876549123",
            account_type=AccountType.SAVINGS,
            balance=Decimal("12850.00"),
        )
        credit = Account(
            user_id=user.id,
            account_number="9876543311",
            account_type=AccountType.CREDIT_CARD,
            balance=Decimal("850.00"),  # Spent
            credit_limit=Decimal("3000.00"),
        )
        db.add_all([checking, savings, credit])
        await db.flush()

        # create mock Ledger Entries
        t1 = Transaction(
            reference_number="TXN-A1B2C3D4E5",
            source_account_id=savings.id,
            destination_account_id=checking.id,
            amount=Decimal("500.00"),
            category=TransactionCategory.TRANSFER,
            status=TransactionStatus.COMPLETED,
            description="Monthly Savings Transfer",
        )
        t2 = Transaction(
            reference_number="TXN-F6G7H8I9J0",
            source_account_id=checking.id,
            destination_account_id=credit.id,
            amount=Decimal("200.00"),
            category=TransactionCategory.PAYMENT,
            status=TransactionStatus.COMPLETED,
            description="Credit Card Bill Payment",
        )
        db.add_all([t1, t2])

        # create Notifications
        n1 = Notification(
            user_id=user.id,
            title="Welcome to FinBank",
            message="Your digital accounts have been successfully provisioned.",
        )
        n2 = Notification(
            user_id=user.id,
            title="Transfer Received",
            message="You received $500.00 into your Checking account ending in 4829.",
        )
        db.add_all([n1, n2])

        await db.commit()
        print(
            "Successfully seeded database with mock user 'john@example.com' / 'password123'"
        )


if __name__ == "__main__":
    asyncio.run(seed_data())
