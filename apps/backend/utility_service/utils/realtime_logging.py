import json
import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
from uuid import UUID

from utility_service.use_cases.dtos.realtime_diagnostics import (
    RealtimeDeliveryOutcome,
    RealtimeDeliveryStage,
    RealtimeEventContext,
    RealtimeFailureReason,
)


_logger = logging.getLogger("utility_service.realtime")
_EVENTS = frozenset(
    {
        "realtime_delivery_failed",
        "realtime_publication_failed",
        "realtime_connection_failed",
        "realtime_cleanup_failed",
    }
)
_DETAILS = frozenset(
    {
        "closeCode",
        "timeoutSeconds",
        "frameBytes",
        "pendingFrames",
        "pendingBytes",
        "maxPendingFrames",
        "maxPendingBytes",
    }
)


def log_realtime_failure(
    *,
    event: str,
    context: RealtimeEventContext | None,
    layer_id: UUID,
    connection_id: UUID | None,
    reason: RealtimeFailureReason,
    stage: RealtimeDeliveryStage,
    outcome: RealtimeDeliveryOutcome | None,
    error: Exception | None = None,
    details: Mapping[str, int | float] | None = None,
) -> None:
    # Diagnostics must not change a committed operation or prevent socket cleanup.
    try:
        if event not in _EVENTS:
            return
        payload = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "layerId": str(layer_id),
            "reason": reason.value,
            "stage": stage.value,
        }
        if context is not None:
            payload.update(
                eventId=context.event_id,
                eventType=context.event_type,
                featureId=str(context.feature_id),
                featureVersion=context.feature_version,
            )
        if connection_id is not None:
            payload["connectionId"] = str(connection_id)
        if outcome is not None:
            payload["outcome"] = outcome.value
        if details:
            payload.update(
                (key, value)
                for key, value in details.items()
                if key in _DETAILS and type(value) in (int, float)
            )
        if error is not None:
            payload["exceptionType"] = type(error).__name__
            frames = []
            traceback = error.__traceback__
            while traceback is not None:
                code = traceback.tb_frame.f_code
                frames.append(
                    {
                        "file": PurePosixPath(PureWindowsPath(code.co_filename).name).name,
                        "function": code.co_name,
                        "line": traceback.tb_lineno,
                    }
                )
                frames = frames[-10:]
                traceback = traceback.tb_next
            payload["stack"] = frames
        _logger.warning(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    except Exception:
        return
