

# from sqlalchemy import insert
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.models.transactions_model import Transaction


# class TransferRepository():
#     def __init__(self, db: AsyncSession):
#         self.db = db

#     async def create_transfer(self, transfer: dict):
#         result = await self.db.execute(
#             insert(Transfer).values(**transfer)
#         )
#         return result
