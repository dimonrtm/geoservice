from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketException, status

from utility_service.use_cases.dtos.realtime_diagnostics import (
    RealtimeDeliveryOutcome,
    RealtimeDeliveryStage,
    RealtimeEventContext,
    RealtimeFailureReason,
)
from utility_service.utils.realtime_logging import log_realtime_failure


@dataclass(frozen=True)
class WebSocketUserContext:
    user_id: UUID
    email: str
    role: str
    session_id: UUID


SessionActivityChecker = Callable[[UUID], Awaitable[bool]]


@dataclass(frozen=True)
class QueuedRealtimeFrame:
    text: str
    size_bytes: int
    context: RealtimeEventContext | None = None


@dataclass(eq=False)
class LayerSubscription:
    layer_id: UUID
    socket: WebSocket
    context: WebSocketUserContext
    queue: asyncio.Queue[QueuedRealtimeFrame]
    connection_id: UUID = field(default_factory=uuid4)
    pending_bytes: int = 0
    writer: asyncio.Task | None = None
    current_frame: QueuedRealtimeFrame | None = None
    sending: asyncio.Task | None = None


class WebSocketConnectionManager:
    def __init__(
        self,
        is_session_active: SessionActivityChecker,
        *,
        close_timeout_seconds: float = 1.0,
        send_timeout_seconds: float = 5.0,
        max_pending_frames: int = 32,
        max_pending_bytes: int = 1024 * 1024,
    ) -> None:
        self._is_session_active = is_session_active
        self._close_timeout_seconds = close_timeout_seconds
        self._send_timeout_seconds = send_timeout_seconds
        self._max_pending_frames = max_pending_frames
        self._max_pending_bytes = max_pending_bytes
        self._connections: dict[UUID, dict[WebSocket, LayerSubscription]] = defaultdict(dict)
        self._tasks: set[asyncio.Task] = set()

    def _track(self, coroutine):
        task = asyncio.create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._task_finished)
        return task

    def _task_finished(self, task):
        self._tasks.discard(task)
        if not task.cancelled():
            # Owners (_write/_close) diagnose outcomes; callbacks only consume exceptions.
            task.exception()

    async def connect(
        self, layer_id: UUID, websocket: WebSocket, user_context: WebSocketUserContext
    ) -> None:
        subscription = LayerSubscription(
            layer_id, websocket, user_context, asyncio.Queue(self._max_pending_frames)
        )
        try:
            active = await self._is_session_active(user_context.session_id)
        except Exception as error:
            self._log_failure(
                subscription,
                None,
                RealtimeFailureReason.SESSION_CHECK_FAILED,
                RealtimeDeliveryStage.SESSION_CHECK,
                error=error,
            )
            active = False
        if not active:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Сессия недействительна"
            )
        await websocket.accept()
        self._connections[layer_id][websocket] = subscription
        self._publish((subscription,), {"type": "connected", "layerId": str(layer_id)})
        if self._is_registered(subscription):
            subscription.writer = self._track(self._write(subscription))

    def _is_registered(self, subscription):
        return (
            self._connections.get(subscription.layer_id, {}).get(subscription.socket)
            is subscription
        )

    async def _write(self, subscription: LayerSubscription) -> None:
        try:
            while True:
                frame = await subscription.queue.get()
                subscription.current_frame = frame
                subscription.pending_bytes -= frame.size_bytes
                try:
                    active = await self._is_session_active(subscription.context.session_id)
                except Exception as error:
                    await self.disconnect_session(
                        subscription.context.session_id,
                        failure_reason=RealtimeFailureReason.SESSION_CHECK_FAILED,
                        error=error,
                    )
                    return
                if not self._is_registered(subscription):
                    return
                if not active:
                    await self.disconnect_session(subscription.context.session_id)
                    return
                try:
                    sending = self._track(subscription.socket.send_text(frame.text))
                    subscription.sending = sending
                    done, _ = await asyncio.wait([sending], timeout=self._send_timeout_seconds)
                    if not done:
                        self._retire(
                            subscription, 1013, failure_reason=RealtimeFailureReason.SEND_TIMEOUT
                        )
                        return
                    sending.result()
                except Exception as error:
                    self._retire(
                        subscription,
                        1013,
                        failure_reason=RealtimeFailureReason.SEND_ERROR,
                        error=error,
                    )
                    return
                subscription.current_frame = None
                subscription.sending = None
        except Exception as error:
            self._retire(
                subscription,
                1013,
                failure_reason=RealtimeFailureReason.WRITER_FAILED,
                error=error,
            )
        finally:
            if subscription.sending is not None and not subscription.sending.done():
                subscription.sending.cancel()

    async def broadcast_to_layer(self, layer_id: UUID, event: dict[str, object]) -> None:
        subscriptions = tuple(self._connections.get(layer_id, {}).values())
        if subscriptions:
            self._publish(subscriptions, event)

    def publish_event(
        self, context: RealtimeEventContext, build_event: Callable[[], dict[str, object]]
    ) -> None:
        subscriptions = tuple(self._connections.get(context.layer_id, {}).values())
        if not subscriptions:
            return
        stage = RealtimeDeliveryStage.PREPARE
        try:
            event = build_event()
            stage = RealtimeDeliveryStage.SERIALIZE
            frame = self._serialize(event, context)
        except Exception as error:
            self._publication_failed(subscriptions, context, stage, error)
            return
        for index, subscription in enumerate(subscriptions):
            try:
                self._enqueue(subscription, frame)
            except Exception as error:
                self._publication_failed(
                    subscriptions[index:], context, RealtimeDeliveryStage.ENQUEUE, error
                )
                return

    def _publication_failed(self, subscriptions, context, stage, error):
        for subscription in subscriptions:
            log_realtime_failure(
                event="realtime_delivery_failed",
                context=context,
                layer_id=context.layer_id,
                connection_id=subscription.connection_id,
                reason=RealtimeFailureReason.PUBLICATION_FAILED,
                stage=stage,
                outcome=RealtimeDeliveryOutcome.NOT_SENT,
                error=error,
            )

    def _serialize(self, event, context=None):
        text = json.dumps(event, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return QueuedRealtimeFrame(text, len(text.encode("utf-8")), context)

    def _publish(self, subscriptions, event):
        frame = self._serialize(event)
        for subscription in subscriptions:
            self._enqueue(subscription, frame)

    def _enqueue(self, subscription, frame):
        if frame.size_bytes > self._max_pending_bytes:
            reason = RealtimeFailureReason.FRAME_TOO_LARGE
        elif subscription.queue.full():
            reason = RealtimeFailureReason.QUEUE_FRAMES_EXCEEDED
        elif subscription.pending_bytes + frame.size_bytes > self._max_pending_bytes:
            reason = RealtimeFailureReason.QUEUE_BYTES_EXCEEDED
        else:
            subscription.queue.put_nowait(frame)
            subscription.pending_bytes += frame.size_bytes
            return
        self._retire(subscription, 1013, failure_reason=reason, rejected_frame=frame)

    def _log_failure(
        self,
        subscription,
        frame,
        reason,
        stage,
        *,
        outcome=RealtimeDeliveryOutcome.NOT_SENT,
        error=None,
        details=None,
    ):
        context = frame.context if frame is not None else None
        log_realtime_failure(
            event=(
                "realtime_delivery_failed" if context is not None else "realtime_connection_failed"
            ),
            context=context,
            layer_id=subscription.layer_id,
            connection_id=subscription.connection_id,
            reason=reason,
            stage=stage,
            outcome=outcome,
            error=error,
            details=details,
        )

    def _send_succeeded(self, subscription):
        sending = subscription.sending
        return (
            sending is not None
            and sending.done()
            and not sending.cancelled()
            and sending.exception() is None
        )

    def _retire(
        self,
        subscription,
        code=None,
        *,
        failure_reason=None,
        error=None,
        rejected_frame=None,
        close_code=None,
    ):
        connections = self._connections.get(subscription.layer_id)
        if not connections or connections.pop(subscription.socket, None) is None:
            return None
        if not connections:
            del self._connections[subscription.layer_id]
        details = {
            "pendingFrames": subscription.queue.qsize(),
            "pendingBytes": subscription.pending_bytes,
            "maxPendingFrames": self._max_pending_frames,
            "maxPendingBytes": self._max_pending_bytes,
        }
        if close_code is not None:
            details["closeCode"] = close_code
        if failure_reason == RealtimeFailureReason.SEND_TIMEOUT:
            details["timeoutSeconds"] = self._send_timeout_seconds
        reported_ids = set()

        def report(frame, stage, outcome=RealtimeDeliveryOutcome.NOT_SENT):
            if failure_reason is None or frame is None:
                return
            event_id = frame.context.event_id if frame.context is not None else None
            if event_id in reported_ids:
                return
            reported_ids.add(event_id)
            self._log_failure(
                subscription,
                frame,
                failure_reason,
                stage,
                outcome=outcome,
                error=error,
                details={**details, "frameBytes": frame.size_bytes},
            )

        if self._send_succeeded(subscription):
            if subscription.current_frame is not None:
                context = subscription.current_frame.context
                reported_ids.add(context.event_id if context else None)
        elif subscription.sending is not None:
            report(
                subscription.current_frame,
                RealtimeDeliveryStage.SEND,
                RealtimeDeliveryOutcome.SEND_UNCONFIRMED,
            )
        else:
            report(subscription.current_frame, RealtimeDeliveryStage.SESSION_CHECK)
        report(rejected_frame, RealtimeDeliveryStage.ENQUEUE)
        while not subscription.queue.empty():
            report(subscription.queue.get_nowait(), RealtimeDeliveryStage.QUEUE_DISCARD)
        if failure_reason == RealtimeFailureReason.WRITER_FAILED and not reported_ids:
            self._log_failure(
                subscription,
                None,
                failure_reason,
                RealtimeDeliveryStage.QUEUE_DISCARD,
                outcome=None,
                error=error,
                details=details,
            )
        subscription.pending_bytes = 0
        subscription.current_frame = None
        if subscription.sending is not None and not subscription.sending.done():
            subscription.sending.cancel()
        if subscription.writer and subscription.writer is not asyncio.current_task():
            subscription.writer.cancel()
        if code is not None:
            return self._track(self._close(subscription, code))
        return None

    async def _close(self, subscription, code):
        def report(reason, error=None):
            log_realtime_failure(
                event="realtime_cleanup_failed",
                context=None,
                layer_id=subscription.layer_id,
                connection_id=subscription.connection_id,
                reason=reason,
                stage=RealtimeDeliveryStage.CLOSE,
                outcome=None,
                error=error,
                details={"closeCode": code, "timeoutSeconds": self._close_timeout_seconds},
            )

        async def close_transport():
            try:
                await subscription.socket.close(code=code)
            except Exception as error:
                report(RealtimeFailureReason.CLOSE_ERROR, error)

        task = self._track(close_transport())
        try:
            done, _ = await asyncio.wait([task], timeout=self._close_timeout_seconds)
            if not done:
                report(RealtimeFailureReason.CLOSE_TIMEOUT)
        finally:
            if not task.done():
                task.cancel()

    async def disconnect(
        self,
        layer_id: UUID,
        websocket: WebSocket,
        *,
        close_code: int | None = None,
        failure_reason: RealtimeFailureReason | None = None,
        error: Exception | None = None,
    ) -> None:
        subscription = self._connections.get(layer_id, {}).get(websocket)
        if subscription:
            self._retire(
                subscription, failure_reason=failure_reason, error=error, close_code=close_code
            )

    async def disconnect_session(
        self, session_id: UUID, *, failure_reason=None, error=None
    ) -> None:
        subscriptions = [
            subscription
            for connections in self._connections.values()
            for subscription in connections.values()
            if subscription.context.session_id == session_id
        ]
        closing = [
            self._retire(subscription, 1008, failure_reason=failure_reason, error=error)
            for subscription in subscriptions
        ]
        if closing:
            await asyncio.gather(*(task for task in closing if task is not None))

    async def shutdown(self) -> None:
        for connections in tuple(self._connections.values()):
            for subscription in tuple(connections.values()):
                self._retire(subscription, 1001)
        if self._tasks:
            # Let each close owner observe its own deadline before cancelling remaining tasks.
            _, pending = await asyncio.wait(
                tuple(self._tasks), timeout=2 * self._close_timeout_seconds
            )
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.wait(pending, timeout=self._close_timeout_seconds)

    def get_connection_count(self, layer_id: UUID) -> int:
        return len(self._connections.get(layer_id, {}))
