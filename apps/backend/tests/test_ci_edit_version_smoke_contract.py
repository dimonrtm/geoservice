import io
import json
import re
import shlex
import urllib.error
import urllib.request
from pathlib import Path

import pytest


def test_ci_authenticated_version_smoke_uses_current_read_endpoint(monkeypatch) -> None:
    workflow = next(
        (
            parent / ".github/workflows/ci.yml"
            for parent in Path(__file__).resolve().parents
            if (parent / ".github/workflows/ci.yml").exists()
        ),
        None,
    )
    if workflow is None:
        pytest.skip("Repository CI workflow is unavailable in the backend-only image.")
    source = workflow.read_text(encoding="utf-8")
    # Select the inline smoke that opens a version before reading its geometry.
    scripts = re.findall(r'python -c \\\n\s*(".*?")(?=\n)', source, re.DOTALL)
    script = next(script for script in scripts if "open_request=" in script)
    script = shlex.split(script.replace("\\\n", ""))[0]
    work_order_id = "6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401"
    version_id = "test-version"
    base = "http://127.0.0.1:8000/api/v1"
    version_url = f"{base}/work-orders/{work_order_id}/edit-versions"
    routes = {
        ("POST", f"{base}/auth/login"): {"access_token": "test-token"},
        ("POST", version_url): {"editVersion": {"id": version_id}},
        ("GET", f"{version_url}/{version_id}"): {
            "workOrder": {
                "id": work_order_id,
                "scope": {"aoi": {"id": "6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0100"}},
                "editVersion": {
                    "id": version_id,
                    "features": {"features": [{}] * 19},
                    "associations": [{}] * 9,
                },
            },
        },
    }
    calls = []

    def urlopen(request):
        route = (request.get_method(), request.full_url)
        calls.append(route)
        if route not in routes:
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)
        if route[1] != f"{base}/auth/login":
            assert request.get_header("Authorization") == "Bearer test-token"
        return io.BytesIO(json.dumps(routes[route]).encode())

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    exec(compile(script, str(workflow), "exec"), {})
    assert calls == list(routes)
