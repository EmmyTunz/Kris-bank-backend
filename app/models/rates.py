from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class Rate(Base):
    __tablename__ = "rates"
    id: Mapped[int] = mapped_column(primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(3))
    target_currency: Mapped[str] = mapped_column(String(3))
    rate: Mapped[float] = mapped_column(Numeric(15, 4))
