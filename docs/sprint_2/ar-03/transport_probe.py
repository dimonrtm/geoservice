"""Изолированная проверка Uvicorn transport и stdout/stderr без production auth/DB."""

import asyncio
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
from uuid import UUID

os.environ.setdefault("DEV_MODE", "true")
os.environ.setdefault("JWT_SECRET", "ar03-probe-only")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/unused"
)
sys.path.insert(0, "/app")


def build_probe_app():
    from fastapi import FastAPI, WebSocket
    from utility_service.use_cases.dtos.realtime_diagnostics import RealtimeEventContext
    from utility_service.use_cases.services.realtime_connection_manager import (
        WebSocketConnectionManager,
        WebSocketUserContext,
    )
    from utility_service.web_api.api.ws_layers import subscribe_to_layer_updates

    async def active(_):
        return True

    manager = WebSocketConnectionManager(active)
    app = FastAPI()
    layer = UUID(int=1)
    context = WebSocketUserContext(
        UUID(int=2), "probe@example.invalid", "editor", UUID(int=3)
    )

    @app.websocket("/probe")
    async def subscribe(websocket: WebSocket):
        await subscribe_to_layer_updates(websocket, layer, context, manager)

    @app.post("/publish-failure")
    async def publish_failure():
        def build_event():
            raise ValueError("SECRET must not appear")

        manager.publish_event(
            RealtimeEventContext("evt_probe", "feature_updated", layer, UUID(int=4), 2),
            build_event,
        )
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"ok": True}

    async def observe(scope, receive, send):
        async def observed_receive():
            message = await receive()
            if message["type"] == "websocket.disconnect":
                print("OBSERVED_CLOSE=" + str(message.get("code")), flush=True)
            return message

        await app(scope, observed_receive, send)

    return observe


async def probe(port):
    import httpx
    from websockets.frames import Close
    from websockets.legacy.client import connect

    async with httpx.AsyncClient() as client:
        for _ in range(100):
            try:
                response = await client.get(f"http://127.0.0.1:{port}/health")
                if response.status_code == 200:
                    break
            except httpx.TransportError:
                pass
            await asyncio.sleep(0.05)
        else:
            raise AssertionError("Probe server did not start")
        for closing in ("normal", "empty", "abort"):
            websocket = await connect(f"ws://127.0.0.1:{port}/probe")
            assert json.loads(await websocket.recv())["type"] == "connected"
            if closing == "normal":
                response = await client.post(f"http://127.0.0.1:{port}/publish-failure")
                assert response.json() == {"ok": True}
                await websocket.close(code=1000)
            elif closing == "empty":
                await websocket.write_close_frame(Close(1005, ""), data=b"")
                await websocket.wait_closed()
            else:
                websocket.transport.abort()
                await websocket.wait_closed()
        # The next HTTP roundtrip allows the receive handler to process the last disconnect.
        await client.get(f"http://127.0.0.1:{port}/health")


def main():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    with tempfile.TemporaryDirectory() as directory:
        output_path = Path(directory) / "server.log"
        with output_path.open("wb") as output:
            process = subprocess.Popen(
                [sys.executable, __file__, "serve", str(port)],
                stdout=output,
                stderr=output,
            )
            try:
                asyncio.run(probe(port))
            finally:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        log = output_path.read_text()
        assert process.returncode == 0, log
        assert "SECRET" not in log, log
        codes = [
            int(line.split("=")[1])
            for line in log.splitlines()
            if line.startswith("OBSERVED_CLOSE=")
        ]
        assert codes == [1000, 1005, 1006], log
        records = [
            json.loads(line)
            for line in log.splitlines()
            if line.startswith('{"event":')
        ]
        failures = [
            item for item in records if item["event"] == "realtime_delivery_failed"
        ]
        assert len(failures) == 1, log
        assert failures[0]["eventId"] == "evt_probe"
        assert failures[0]["connectionId"]
        assert failures[0]["reason"] == "publication_failed"
        print(
            json.dumps(
                {"closeCodes": codes, "processLog": failures[0], "passed": True},
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        import uvicorn

        uvicorn.run(build_probe_app(), host="127.0.0.1", port=int(sys.argv[2]))
    else:
        main()
