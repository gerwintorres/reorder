from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, Response, status
from sqlalchemy.orm import Session

from reorder.api.errors import ApiError
from reorder.db.session import get_db
from reorder.repositories.products import DuplicateSkuError, ProductRepository
from reorder.schemas.errors import ErrorsOut
from reorder.schemas.products import Page, ProductIn, ProductOut

# Every product belongs to user 1 until requests are authenticated.
OWNER_ID = 1
MAX_PAGE_SIZE = 200
# Largest value of a PostgreSQL INTEGER; a larger id fails in the database.
MAX_ID = 2**31 - 1

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorsOut}},
)


def get_products(db: Annotated[Session, Depends(get_db)]) -> ProductRepository:
    """Provide a product repository on the request's session."""
    return ProductRepository(db)


Products = Annotated[ProductRepository, Depends(get_products)]
ProductId = Annotated[int, Path(ge=1, le=MAX_ID)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorsOut}},
)
def create_product(
    payload: ProductIn, products: Products, request: Request, response: Response
) -> ProductOut:
    """Create a product. Its SKU must be new for the owner."""
    try:
        product = products.add(OWNER_ID, payload.sku, payload.name)
    except DuplicateSkuError as error:
        raise ApiError(status.HTTP_409_CONFLICT, "sku", str(error)) from error
    response.headers["Location"] = request.url_for(
        "get_product", product_id=product.id
    ).path
    return ProductOut.model_validate(product)


@router.get(
    "/{product_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorsOut}},
)
def get_product(product_id: ProductId, products: Products) -> ProductOut:
    """Return one of the owner's products."""
    product = products.get(product_id, OWNER_ID)
    if product is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND, "product_id", f"Product {product_id} not found"
        )
    return ProductOut.model_validate(product)


@router.get("")
def list_products(
    products: Products,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ProductOut]:
    """Return one page of the owner's products, sorted by SKU."""
    page = products.list_for_owner(OWNER_ID, limit, offset)
    return Page(
        items=[ProductOut.model_validate(product) for product in page],
        total=products.count_for_owner(OWNER_ID),
        limit=limit,
        offset=offset,
    )
