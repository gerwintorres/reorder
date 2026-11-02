from fastapi.testclient import TestClient

from reorder.api.main import app

client = TestClient(app)

URL = "/api/v1/estimate/preview"


def test_validation_errors_use_the_api_error_format() -> None:
    response = client.post(URL, json={})
    body = response.json()
    assert (response.status_code, set(body)) == (422, {"errors"})


def test_each_error_has_only_field_and_message() -> None:
    errors = client.post(URL, json={}).json()["errors"]
    assert all(set(error) == {"field", "message"} for error in errors)


def test_missing_field_is_named_without_body_prefix() -> None:
    errors = client.post(URL, json={}).json()["errors"]
    assert {"field": "cutoff_date", "message": "Field required"} in errors


def test_malformed_json_is_reported_on_body() -> None:
    response = client.post(
        URL, content=b"{bad json", headers={"content-type": "application/json"}
    )
    assert [error["field"] for error in response.json()["errors"]] == ["body"]


def test_openapi_documents_the_api_error_format() -> None:
    spec = client.get("/openapi.json").json()
    response = spec["paths"][URL]["post"]["responses"]["422"]
    schema = response["content"]["application/json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/ErrorsOut"}
