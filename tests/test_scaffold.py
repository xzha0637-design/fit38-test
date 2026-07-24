from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.version import APP_VERSION, MODEL_CONTRACT_VERSION


def test_application_shell_and_versioned_contract_are_available() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    page = client.get("/")
    schema = client.get("/openapi.json")

    assert page.status_code == 200
    assert "Signal Review" in page.text
    assert "Triage evidence, not a verdict." in page.text
    assert schema.status_code == 200
    assert schema.json()["info"]["version"] == APP_VERSION
    assert MODEL_CONTRACT_VERSION == "model-contract-v1"


def test_unknown_route_uses_controlled_http_error() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/not-a-route")

    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
