from pydantic import BaseModel, ConfigDict, Field


class ProductIn(BaseModel):
    # Trimmed, so "A-100 " can't become a second product next to "A-100".
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{"sku": "A-100", "name": "Oil filter"}]},
    )

    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str


class Page[T](BaseModel):
    """One page of a list, with the total number of items across all pages."""

    items: list[T]
    total: int
    limit: int
    offset: int
