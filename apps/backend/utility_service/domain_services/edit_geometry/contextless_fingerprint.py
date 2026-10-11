"""Идентичность раннего отказа, не зависящая от ремонта baseline."""

import hashlib

from utility_service.domain_services.edit_geometry.canonicalization import quantize_ordinate
from utility_service.domain_services.edit_geometry.fingerprint import (
    canonical_bytes,
    geometry_document,
)
from utility_service.domain_services.edit_geometry.canonicalization import decimal_text
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.structure import validate_geometry_value
from utility_service.domain_services.edit_geometry.types import FingerprintContext, GeometryValue


def contextless_fingerprint_payload(
    context: FingerprintContext,
    policy: GeometryPolicy,
    geometry: GeometryValue,
) -> bytes:
    validate_geometry_value(geometry)
    rounded = GeometryValue(
        geometry.type,
        tuple(
            tuple(
                quantize_ordinate(
                    v,
                    policy,
                )
                for v in p
            )
            for p in geometry.coordinates
        ),
        geometry.srid,
    )
    return canonical_bytes(
        {
            "fingerprintVersion": 1,
            "identityMode": "contextless",
            "commandType": "replace_feature_geometry",
            "workOrderId": str(context.work_order_id),
            "editVersionId": str(context.edit_version_id),
            "featureId": str(context.feature_id),
            "actorUserId": str(context.actor_user_id),
            "baseline": {
                "defaultStateId": str(context.default_state_id),
                "networkRevision": context.base_network_revision,
            },
            "draftVersionToken": context.draft_version_token,
            "geometryPolicy": {
                "version": policy.version,
                "xyResolution": decimal_text(policy.xy_resolution),
                "roundingMode": policy.rounding_mode,
                "srid": 4326,
                "origin": ["0", "0"],
            },
            "geometryRepresentation": "grid_aligned",
            "geometry": geometry_document(rounded),
        }
    )


def contextless_command_fingerprint(
    context: FingerprintContext,
    policy: GeometryPolicy,
    geometry: GeometryValue,
) -> str:
    return (
        "geom-contextless-v1:sha256:"
        + hashlib.sha256(
            contextless_fingerprint_payload(
                context,
                policy,
                geometry,
            )
        ).hexdigest()
    )
