from pydantic import BaseModel


class ErrorItem(BaseModel):
    field: str
    message: str


class ErrorsOut(BaseModel):
    errors: list[ErrorItem]
