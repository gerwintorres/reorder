from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from reorder.api.main import app
from reorder.api.routers.products import MAX_ID, OWNER_ID, get_products
from reorder.db.models import Product
from reorder.repositories.products import DuplicateSkuError

URL = "/api/v1/products"
OTHER_OWNER = OWNER_ID + 1
FILTER = {"sku": "A-100", "name": "Oil filter"}


class FakeProducts:
    """In-memory stand-in for ProductRepository, so these tests need no database."""

    def __init__(self):
        self.rows: list[Product] = []

    def add(self, owner_id: int, sku: str, name: str) -> Product:
        if any(row.owner_id == owner_id and row.sku == sku for row in self.rows):
            raise DuplicateSkuError(sku)
        product = Product(id=len(self.rows) + 1, owner_id=owner_id, sku=sku, name=name)
        self.rows.append(product)
        return product

    def get(self, product_id: int, owner_id: int) -> Product | None:
        matches = (r for r in self.rows if (r.id, r.owner_id) == (product_id, owner_id))
        return next(matches, None)

    def list_for_owner(self, owner_id: int, limit: int, offset: int) -> list[Product]:
        owned = sorted(self.owned_by(owner_id), key=lambda row: row.sku)
        return owned[offset : offset + limit]

    def count_for_owner(self, owner_id: int) -> int:
        return len(self.owned_by(owner_id))

    def owned_by(self, owner_id: int) -> list[Product]:
        return [row for row in self.rows if row.owner_id == owner_id]


@pytest.fixture
def products() -> Iterator[FakeProducts]:
    fake = FakeProducts()
    app.dependency_overrides[get_products] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_products)


@pytest.fixture
def client(products: FakeProducts) -> TestClient:
    return TestClient(app)


def error_fields(response: Any) -> list[str]:
    return [error["field"] for error in response.json()["errors"]]


def test_create_returns_201_with_the_new_product(client: TestClient) -> None:
    response = client.post(URL, json=FILTER)
    assert (response.status_code, response.json()) == (
        201,
        {"id": 1, "sku": "A-100", "name": "Oil filter"},
    )


def test_create_points_location_to_the_new_product(client: TestClient) -> None:
    location = client.post(URL, json=FILTER).headers["location"]
    assert (location, client.get(location).status_code) == (f"{URL}/1", 200)


def test_create_saves_the_product_for_the_fixed_owner(
    client: TestClient, products: FakeProducts
) -> None:
    client.post(URL, json=FILTER)
    assert products.rows[0].owner_id == OWNER_ID


def test_create_trims_spaces_around_sku_and_name(client: TestClient) -> None:
    body = client.post(URL, json={"sku": "  A-100 ", "name": " Oil filter "}).json()
    assert (body["sku"], body["name"]) == ("A-100", "Oil filter")


def test_create_accepts_the_longest_sku_and_name(client: TestClient) -> None:
    response = client.post(URL, json={"sku": "S" * 64, "name": "N" * 255})
    assert response.status_code == 201


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"sku": "", "name": "Oil filter"}, "sku"),
        ({"sku": "   ", "name": "Oil filter"}, "sku"),
        ({"sku": "S" * 65, "name": "Oil filter"}, "sku"),
        ({"sku": "A-100", "name": " "}, "name"),
        ({"sku": "A-100", "name": "N" * 256}, "name"),
        ({"sku": "A-100"}, "name"),
    ],
)
def test_create_rejects_an_invalid_product(
    client: TestClient, payload: dict[str, str], field: str
) -> None:
    response = client.post(URL, json=payload)
    assert (response.status_code, error_fields(response)) == (422, [field])


def test_create_rejects_a_repeated_sku_with_409(client: TestClient) -> None:
    client.post(URL, json=FILTER)
    response = client.post(URL, json={"sku": "A-100", "name": "Copy"})
    assert (response.status_code, response.json()) == (
        409,
        {"errors": [{"field": "sku", "message": "SKU A-100 already exists"}]},
    )


def test_create_allows_the_same_sku_for_another_owner(
    client: TestClient, products: FakeProducts
) -> None:
    products.add(OTHER_OWNER, "A-100", "Oil filter")
    assert client.post(URL, json=FILTER).status_code == 201


def test_get_returns_the_product(client: TestClient) -> None:
    client.post(URL, json=FILTER)
    response = client.get(f"{URL}/1")
    assert (response.status_code, response.json()) == (
        200,
        {"id": 1, "sku": "A-100", "name": "Oil filter"},
    )


def test_get_returns_404_for_a_missing_product(client: TestClient) -> None:
    response = client.get(f"{URL}/99")
    assert (response.status_code, response.json()) == (
        404,
        {"errors": [{"field": "product_id", "message": "Product 99 not found"}]},
    )


def test_get_returns_404_for_another_owners_product(
    client: TestClient, products: FakeProducts
) -> None:
    products.add(OTHER_OWNER, "B-200", "Belt")
    assert client.get(f"{URL}/1").status_code == 404


def test_get_accepts_the_largest_id_the_database_stores(client: TestClient) -> None:
    assert client.get(f"{URL}/{MAX_ID}").status_code == 404


@pytest.mark.parametrize("product_id", [0, MAX_ID + 1])
def test_get_rejects_an_id_out_of_range(client: TestClient, product_id: int) -> None:
    response = client.get(f"{URL}/{product_id}")
    assert (response.status_code, error_fields(response)) == (422, ["product_id"])


def test_list_returns_a_page_sorted_by_sku(client: TestClient) -> None:
    for sku in ("C-3", "A-1", "B-2"):
        client.post(URL, json={"sku": sku, "name": sku})
    body = client.get(URL, params={"limit": 2, "offset": 1}).json()
    assert ([item["sku"] for item in body["items"]], body["total"]) == (
        ["B-2", "C-3"],
        3,
    )


def test_list_echoes_limit_and_offset(client: TestClient) -> None:
    body = client.get(URL, params={"limit": 2, "offset": 1}).json()
    assert (body["limit"], body["offset"]) == (2, 1)


def test_list_only_includes_the_owners_products(
    client: TestClient, products: FakeProducts
) -> None:
    products.add(OTHER_OWNER, "B-200", "Belt")
    client.post(URL, json=FILTER)
    body = client.get(URL).json()
    assert ([item["sku"] for item in body["items"]], body["total"]) == (["A-100"], 1)


def test_list_defaults_to_50_items_from_the_start(client: TestClient) -> None:
    assert client.get(URL).json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_list_accepts_the_maximum_page_size(client: TestClient) -> None:
    assert client.get(URL, params={"limit": 200}).status_code == 200


@pytest.mark.parametrize(
    ("params", "field"),
    [({"limit": 201}, "limit"), ({"limit": 0}, "limit"), ({"offset": -1}, "offset")],
)
def test_list_rejects_invalid_paging(
    client: TestClient, params: dict[str, int], field: str
) -> None:
    response = client.get(URL, params=params)
    assert (response.status_code, error_fields(response)) == (422, [field])


@pytest.mark.parametrize(
    ("path", "method", "status_code"),
    [(URL, "post", "409"), (URL + "/{product_id}", "get", "404")],
)
def test_openapi_documents_errors_with_the_api_error_format(
    client: TestClient, path: str, method: str, status_code: str
) -> None:
    responses = client.get("/openapi.json").json()["paths"][path][method]["responses"]
    schema = responses[status_code]["content"]["application/json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/ErrorsOut"}
