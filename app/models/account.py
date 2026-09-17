from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    account_number: Mapped[str] = mapped_column(String(10), unique=True)

    balance: Mapped[float] = mapped_column(Numeric(15, 2))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

