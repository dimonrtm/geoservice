from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


@dataclass(frozen=True)
class RealtimeEventContext:
    event_id: str
    event_type: str
    layer_id: UUID
    feature_id: UUID
    feature_version: int


class RealtimeFailureReason(StrEnum):
    PUBLICATION_FAILED = "publication_failed"
    FRAME_TOO_LARGE = "frame_too_large"
    QUEUE_FRAMES_EXCEEDED = "queue_frames_exceeded"
    QUEUE_BYTES_EXCEEDED = "queue_bytes_exceeded"
    SEND_TIMEOUT = "send_timeout"
    SEND_ERROR = "send_error"
    ABNORMAL_DISCONNECT = "abnormal_disconnect"
    DISCONNECT_UNKNOWN = "disconnect_unknown"
    SESSION_CHECK_FAILED = "session_check_failed"
    WRITER_FAILED = "writer_failed"
    CLOSE_ERROR = "close_error"
    CLOSE_TIMEOUT = "close_timeout"


class RealtimeDeliveryStage(StrEnum):
    PREPARE = "prepare"
    SERIALIZE = "serialize"
    ENQUEUE = "enqueue"
    SESSION_CHECK = "session_check"
    SEND = "send"
    QUEUE_DISCARD = "queue_discard"
    CLOSE = "close"


class RealtimeDeliveryOutcome(StrEnum):
    NOT_SENT = "not_sent"
    SEND_UNCONFIRMED = "send_unconfirmed"
