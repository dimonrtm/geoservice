from fastapi.testclient import TestClient

from utility_service.web_api.tests.test_geometry_save_api import api_context


def test_put_cors_preflight():
    from utility_service.web_api.main import app
    from utility_service.utils.settings import settings

    client = TestClient(app)
    origin = settings.cors_origins[0]
    response = client.options(
        "/api/v1/work-orders/test/edit-versions/test/features/test/geometry",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200, response.text
    assert "PUT" in response.headers["access-control-allow-methods"]
    denied = client.options(
        "/api/v1/work-orders/test/edit-versions/test/features/test/geometry",
        headers={
            "Origin": "https://untrusted.invalid",
            "Access-Control-Request-Method": "PUT",
        },
    )
    assert denied.status_code == 400


def test_openapi_documents_strict_put_and_errors():
    client, *_ = api_context()
    doc = client.get("/openapi.json").json()
    prefix = "/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}"
    save = doc["paths"][prefix + "/features/{feature_id}/geometry"]["put"]
    body = save["requestBody"]["content"]["application/json"]["schema"]
    assert body["additionalProperties"] is False
    assert set(body["required"]) == {"commandId", "draftVersionToken", "geometry"}
    assert body["properties"]["geometry"]["properties"]["type"]["const"] == "LineString"
    assert body["properties"]["geometry"]["properties"]["coordinates"]["minItems"] == 2
    for operation in (save, doc["paths"][prefix + "/workspace"]["get"]):
        error = operation["responses"]["422"]["content"]["application/json"]["schema"]
        error = doc["components"]["schemas"][error["$ref"].split("/")[-1]]
        assert set(error["required"]) == {"code", "message", "correlationId"}
        assert error["additionalProperties"] is False


def test_openapi_matches_save_and_workspace():
    client, *_ = api_context()
    doc = client.get("/openapi.json").json()

    def resolve(schema):
        if "$ref" not in schema:
            return schema
        node = doc
        assert schema["$ref"].startswith("#/")
        for part in schema["$ref"][2:].split("/"):
            node = node[part]
        return node

    def check_refs(node):
        if isinstance(
            node,
            dict,
        ):
            if "$ref" in node:
                resolve(node)
            for value in node.values():
                check_refs(value)
        elif isinstance(
            node,
            list,
        ):
            for value in node:
                check_refs(value)

    check_refs(doc)
    prefix = "/api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}"
    save = doc["paths"][prefix + "/features/{feature_id}/geometry"]["put"]
    get = doc["paths"][prefix + "/workspace"]["get"]
    for operation in (save, get):
        for parameter in operation["parameters"]:
            if parameter["in"] == "path":
                assert parameter["required"] is True
                assert parameter["schema"]["format"] == "uuid"
        for status in (401, 403, 404, 409, 422, 500):
            schema = resolve(
                operation["responses"][str(status)]["content"]["application/json"]["schema"]
            )
            assert set(schema["properties"]) == {"code", "message", "correlationId"}
    request_schema = save["requestBody"]["content"]["application/json"]["schema"]
    position = request_schema["properties"]["geometry"]["properties"]["coordinates"]["items"]
    assert position["minItems"] == position["maxItems"] == 2
    assert [item["maximum"] for item in position["prefixItems"]] == [180, 90]
    assert "64" in request_schema["description"] and "324" in request_schema["description"]
    saved = resolve(save["responses"]["200"]["content"]["application/json"]["schema"])
    assert "basicValidation" in saved["required"]
    assert {
        "type": "null",
    } in saved["properties"][
        "basicValidation"
    ]["anyOf"]
    workspace = resolve(get["responses"]["200"]["content"]["application/json"]["schema"])
    work_order = resolve(workspace["properties"]["workOrder"])
    version = resolve(work_order["properties"]["editVersion"])
    for field in ("draftVersionToken", "hasPersistedChangeSet", "basicValidation", "changeSet"):
        assert field in version["required"]
    for field in ("basicValidation", "changeSet"):
        assert {
            "type": "null",
        } in version["properties"][
            field
        ]["anyOf"]
    change_set = resolve(
        next(item for item in version["properties"]["changeSet"]["anyOf"] if "$ref" in item)
    )
    assert set(change_set["required"]) == {
        "featureId",
        "vertexIndex",
        "baselineGeometry",
        "operation",
    }
    opened = doc["paths"]["/api/v1/work-orders/{work_order_id}/edit-versions"]["post"]
    assert "201" in opened["responses"]
    old_validation = resolve(opened["responses"]["422"]["content"]["application/json"]["schema"])
    assert "detail" in old_validation["properties"]
