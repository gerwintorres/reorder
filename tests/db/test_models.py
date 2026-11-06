import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from reorder.db.models import Base, Product, User, WeeklySale


def ddl(model: type[Base]) -> str:
    # Compiled for PostgreSQL without connecting: the SQL the database would run.
    create = CreateTable(model.__table__)
    return " ".join(str(create.compile(dialect=postgresql.dialect())).split())


def test_tables_are_named_in_plural() -> None:
    assert set(Base.metadata.tables) == {"users", "products", "weekly_sales"}


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        (User, "email VARCHAR(320) NOT NULL"),
        (User, "hashed_password VARCHAR(255) NOT NULL"),
        (Product, "owner_id INTEGER NOT NULL"),
        (Product, "sku VARCHAR(64) NOT NULL"),
        (Product, "name VARCHAR(255) NOT NULL"),
        (WeeklySale, "product_id INTEGER NOT NULL"),
        (WeeklySale, "week_start DATE NOT NULL"),
        (WeeklySale, "qty INTEGER NOT NULL"),
        (WeeklySale, "revenue NUMERIC(14, 2) NOT NULL"),
        (WeeklySale, "profit NUMERIC(14, 2) NOT NULL"),
    ],
)
def test_column_types_and_nullability(model: type[Base], expected: str) -> None:
    assert expected in ddl(model)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        (User, "CONSTRAINT pk_users PRIMARY KEY (id)"),
        (Product, "CONSTRAINT pk_products PRIMARY KEY (id)"),
        (WeeklySale, "CONSTRAINT pk_weekly_sales PRIMARY KEY (id)"),
    ],
)
def test_primary_keys(model: type[Base], expected: str) -> None:
    assert expected in ddl(model)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        (User, "CONSTRAINT uq_users_email UNIQUE (email)"),
        (Product, "CONSTRAINT uq_products_owner_id_sku UNIQUE (owner_id, sku)"),
        (
            WeeklySale,
            "CONSTRAINT uq_weekly_sales_product_id_week_start "
            "UNIQUE (product_id, week_start)",
        ),
    ],
)
def test_unique_constraints(model: type[Base], expected: str) -> None:
    assert expected in ddl(model)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        (
            Product,
            "CONSTRAINT fk_products_owner_id_users "
            "FOREIGN KEY(owner_id) REFERENCES users (id)",
        ),
        (
            WeeklySale,
            "CONSTRAINT fk_weekly_sales_product_id_products "
            "FOREIGN KEY(product_id) REFERENCES products (id)",
        ),
    ],
)
def test_foreign_keys(model: type[Base], expected: str) -> None:
    assert expected in ddl(model)


def test_weekly_sale_rejects_negative_qty() -> None:
    assert "CONSTRAINT ck_weekly_sales_qty_non_negative CHECK (qty >= 0)" in ddl(
        WeeklySale
    )


def test_profit_can_be_negative() -> None:
    assert "profit >=" not in ddl(WeeklySale)


@pytest.mark.parametrize("model", [Product, WeeklySale])
def test_unique_constraints_already_provide_the_composite_indexes(
    model: type[Base],
) -> None:
    # PostgreSQL backs each UNIQUE with an index: declaring another would
    # duplicate it and slow down every write.
    assert model.__table__.indexes == set()
