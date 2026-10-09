import hashlib
import json

from utility_service.domain_services.edit_geometry.canonicalization import decimal_text
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.structure import validate_geometry_value
from utility_service.domain_services.edit_geometry.types import (
    FingerprintContext,
    GeometryValue,
    PreparedGeometry,
)


def canonical_bytes(value: dict) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def geometry_document(value: GeometryValue) -> dict:
    validate_geometry_value(value)
    positions = [[decimal_text(v) for v in p] for p in value.coordinates]
    return {
        "type": value.type,
        "coordinates": positions[0] if value.type == "Point" else positions,
    }


def baseline_structure_hash(baseline: GeometryValue) -> str:
    document = {
        "dimensions": 2,
        "format": "baseline-structure-v1",
        "geometry": geometry_document(baseline),
        "partCount": 1,
        "srid": baseline.srid,
        "vertexCounts": [len(baseline.coordinates)],
    }
    return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()


def fingerprint_payload(
    context: FingerprintContext,
    baseline: GeometryValue,
    policy: GeometryPolicy,
    prepared: PreparedGeometry,
) -> bytes:
    return canonical_bytes(
        {
            "fingerprintVersion": 1,
            "commandType": "replace_feature_geometry",
            "workOrderId": str(context.work_order_id),
            "editVersionId": str(context.edit_version_id),
            "featureId": str(context.feature_id),
            "actorUserId": str(context.actor_user_id),
            "baseline": {
                "defaultStateId": str(context.default_state_id),
                "networkRevision": context.base_network_revision,
                "structureHash": baseline_structure_hash(baseline),
            },
            "draftVersionToken": context.draft_version_token,
            "geometryPolicy": {
                "version": policy.version,
                "xyResolution": decimal_text(policy.xy_resolution),
                "roundingMode": policy.rounding_mode,
                "srid": 4326,
                "origin": ["0", "0"],
            },
            "geometryRepresentation": prepared.representation,
            "geometry": geometry_document(prepared.geometry),
            "vertexIndex": prepared.vertex_index,
        },
    )


def command_fingerprint(
    context: FingerprintContext,
    baseline: GeometryValue,
    policy: GeometryPolicy,
    prepared: PreparedGeometry,
) -> str:
    payload = fingerprint_payload(
        context,
        baseline,
        policy,
        prepared,
    )
    return "geom-v1:sha256:" + hashlib.sha256(payload).hexdigest()
