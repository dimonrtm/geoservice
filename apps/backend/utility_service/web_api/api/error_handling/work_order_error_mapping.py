from utility_service.use_cases.domain.exceptions.work_order_operation_error import (
    WorkOrderOperationCode,
)


_STATUS_BY_CODE = {
    WorkOrderOperationCode.WORK_ORDER_ACTOR_NOT_FOUND: 404,
    WorkOrderOperationCode.ROLE_NOT_ALLOWED: 403,
    WorkOrderOperationCode.WORK_ORDER_NOT_FOUND: 404,
    WorkOrderOperationCode.WORK_ORDER_NOT_ASSIGNED: 403,
    WorkOrderOperationCode.WORK_ORDER_STATE_CONFLICT: 409,
    WorkOrderOperationCode.WORK_ORDER_CONTEXT_INVALID: 422,
}


def work_order_error_status(code: WorkOrderOperationCode) -> int:
    return _STATUS_BY_CODE[code]
