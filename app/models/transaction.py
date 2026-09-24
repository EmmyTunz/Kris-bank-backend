from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from app.database.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(50), unique=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 2))
    transaction_type: Mapped[str] = mapped_column(String(20))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    created_at:Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
