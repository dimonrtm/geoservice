from enum import Enum


class WorkOrderOperationCode(str, Enum):
    WORK_ORDER_ACTOR_NOT_FOUND = "WORK_ORDER_ACTOR_NOT_FOUND"
    ROLE_NOT_ALLOWED = "ROLE_NOT_ALLOWED"
    WORK_ORDER_NOT_FOUND = "WORK_ORDER_NOT_FOUND"
    WORK_ORDER_NOT_ASSIGNED = "WORK_ORDER_NOT_ASSIGNED"
    WORK_ORDER_STATE_CONFLICT = "WORK_ORDER_STATE_CONFLICT"
    WORK_ORDER_CONTEXT_INVALID = "WORK_ORDER_CONTEXT_INVALID"


class WorkOrderOperationError(Exception):
    def __init__(self, code: WorkOrderOperationCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
