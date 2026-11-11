from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # Explicit constraint names, so migrations can refer to them instead of
    # relying on the ones PostgreSQL would generate.
    metadata = MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
        }
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("owner_id", "sku"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sku: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))


class WeeklySale(Base):
    __tablename__ = "weekly_sales"
    __table_args__ = (
        UniqueConstraint("product_id", "week_start"),
        CheckConstraint("qty >= 0", name="qty_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    week_start: Mapped[date]
    qty: Mapped[int]
    revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    profit: Mapped[Decimal] = mapped_column(Numeric(14, 2))
