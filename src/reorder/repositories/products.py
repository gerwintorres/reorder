import psycopg
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from reorder.db.models import Product, WeeklySale

SKU_PER_OWNER = "uq_products_owner_id_sku"


class DuplicateSkuError(Exception):
    """The owner already has a product with this SKU."""

    def __init__(self, sku: str):
        super().__init__(f"SKU {sku} already exists")
        self.sku = sku


class ProductRepository:
    """Reads and writes an owner's products and their weekly sales.

    Writes commit right away: each one is a single statement. A use case that
    needs several writes in one transaction will own the commit instead.
    """

    def __init__(self, session: Session):
        self.session = session

    def add(self, owner_id: int, sku: str, name: str) -> Product:
        """Save a new product and return it with its generated id.

        Raises:
            DuplicateSkuError: the owner already has a product with this SKU.
        """
        product = Product(owner_id=owner_id, sku=sku, name=name)
        self.session.add(product)
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            if _violated_constraint(error) == SKU_PER_OWNER:
                raise DuplicateSkuError(sku) from error
            raise
        return product

    def get(self, product_id: int, owner_id: int) -> Product | None:
        """Return the owner's product with this id, or None if there is none."""
        query = select(Product).where(
            Product.id == product_id, Product.owner_id == owner_id
        )
        return self.session.scalars(query).one_or_none()

    def list_for_owner(self, owner_id: int, limit: int, offset: int) -> list[Product]:
        """Return one page of the owner's products, sorted by SKU."""
        query = (
            select(Product)
            .where(Product.owner_id == owner_id)
            .order_by(Product.sku)
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(query))

    def count_for_owner(self, owner_id: int) -> int:
        """Return how many products the owner has."""
        query = (
            select(func.count())
            .select_from(Product)
            .where(Product.owner_id == owner_id)
        )
        return self.session.scalars(query).one()

    def weekly_sales(self, product_id: int) -> list[WeeklySale]:
        """Return the product's weekly sales, oldest week first."""
        query = (
            select(WeeklySale)
            .where(WeeklySale.product_id == product_id)
            .order_by(WeeklySale.week_start)
        )
        return list(self.session.scalars(query))


def _violated_constraint(error: IntegrityError) -> str | None:
    # The driver error carries the name of the constraint that failed.
    if isinstance(error.orig, psycopg.Error):
        return error.orig.diag.constraint_name
    return None
