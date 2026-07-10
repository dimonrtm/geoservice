from pathlib import Path
from typing import get_type_hints

import pytest

from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.web_api.api.auth import (
    get_current_user,
    me,
    require_editor,
    require_legacy_gis_editor,
    require_reviewer,
)
from utility_service.web_api.api.secure_router import ping, ping_write
from utility_service.web_api.api.utility_network import get_feeder
from utility_service.web_api.api.work_orders import (
    get_workspace,
    list_assigned_to_me,
    open_edit_version,
)
from utility_service.web_api.api.ws_layers import issue_layer_websocket_ticket


@pytest.mark.parametrize(
    ("function", "parameter"),
    [
        (require_editor, "user"),
        (require_legacy_gis_editor, "user"),
        (require_reviewer, "user"),
        (me, "user"),
        (ping, "user"),
        (ping_write, "user"),
        (list_assigned_to_me, "user"),
        (open_edit_version, "user"),
        (get_workspace, "user"),
        (get_feeder, "_"),
        (issue_layer_websocket_ticket, "user"),
    ],
)
def test_web_api_auth_parameters_use_auth_user_dto(function, parameter: str) -> None:
    assert get_type_hints(function)[parameter] is AuthUserDTO


def test_auth_dependencies_return_auth_user_dto() -> None:
    assert get_type_hints(get_current_user)["return"] is AuthUserDTO
    assert get_type_hints(require_editor)["return"] is AuthUserDTO
    assert get_type_hints(require_legacy_gis_editor)["return"] is AuthUserDTO
    assert get_type_hints(require_reviewer)["return"] is AuthUserDTO


def test_web_api_source_does_not_import_infrastructure() -> None:
    api_dir = Path(__file__).resolve().parents[1] / "api"
    offenders = [
        path.name
        for path in api_dir.glob("*.py")
        if "utility_service.infrastructure" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
