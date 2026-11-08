import json
import logging
from uuid import UUID

from utility_service.use_cases.dtos.realtime_diagnostics import (
    RealtimeDeliveryOutcome,
    RealtimeDeliveryStage,
    RealtimeEventContext,
    RealtimeFailureReason,
)
from utility_service.utils.realtime_logging import log_realtime_failure


def emit_failure(error=None, details=None):
    log_realtime_failure(
        event="realtime_delivery_failed",
        context=RealtimeEventContext("evt_test", "feature_updated", UUID(int=1), UUID(int=2), 3),
        layer_id=UUID(int=1),
        connection_id=UUID(int=4),
        reason=RealtimeFailureReason.SEND_ERROR,
        stage=RealtimeDeliveryStage.SEND,
        outcome=RealtimeDeliveryOutcome.SEND_UNCONFIRMED,
        error=error,
        details=details,
    )


def test_failure_log_has_searchable_context(caplog):
    emit_failure(details={"timeoutSeconds": 5, "secret": 123})
    record = caplog.records[-1]
    payload = json.loads(record.getMessage())
    assert record.name == "utility_service.realtime"
    assert record.levelno == logging.WARNING
    assert payload["timestamp"].endswith("Z")
    assert payload["eventId"] == "evt_test"
    assert payload["eventType"] == "feature_updated"
    assert payload["featureVersion"] == 3
    assert payload["featureId"] == str(UUID(int=2))
    assert payload["connectionId"] == str(UUID(int=4))
    assert payload["reason"] == "send_error"
    assert payload["outcome"] == "send_unconfirmed"
    assert payload["timeoutSeconds"] == 5
    assert "secret" not in payload


def test_failure_log_limits_safe_stack_and_excludes_exception_secrets(caplog):
    def recurse(depth):
        if depth:
            recurse(depth - 1)
        raise RuntimeError("ticket=SECRET_PAYLOAD")

    try:
        recurse(15)
    except RuntimeError as error:
        emit_failure(error)
    record = caplog.records[-1]
    payload = json.loads(record.getMessage())
    assert record.exc_info is None
    assert "SECRET_PAYLOAD" not in logging.Formatter().format(record)
    assert payload["exceptionType"] == "RuntimeError"
    assert len(payload["stack"]) == 10
    assert all(set(frame) == {"file", "function", "line"} for frame in payload["stack"])
    assert all("/" not in frame["file"] and "\\" not in frame["file"] for frame in payload["stack"])


def test_handler_failure_does_not_escape():
    class FailingHandler(logging.Handler):
        def emit(self, record):
            raise OSError("sink unavailable")

    logger = logging.getLogger("utility_service.realtime")
    handler = FailingHandler()
    logger.addHandler(handler)
    try:
        emit_failure()
    finally:
        logger.removeHandler(handler)
