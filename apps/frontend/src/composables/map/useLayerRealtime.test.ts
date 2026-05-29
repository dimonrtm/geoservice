import { beforeEach, describe, expect, it, vi } from "vitest";

type MessageListener = (event: { data: string }) => void;
type CloseListener = (event: { code: number; reason?: string }) => void;
type OpenListener = () => void;

class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances: FakeWebSocket[] = [];

  readonly url: string;
  readyState = FakeWebSocket.CONNECTING;
  private messageListeners = new Set<MessageListener>();
  private closeListeners = new Set<CloseListener>();
  private openListeners = new Set<OpenListener>();

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  static reset(): void {
    FakeWebSocket.instances = [];
  }

  addEventListener(
    type: "message" | "close" | "open",
    listener: MessageListener | CloseListener | OpenListener,
  ): void {
    if (type === "message") {
      this.messageListeners.add(listener as MessageListener);
      return;
    }
    if (type === "close") {
      this.closeListeners.add(listener as CloseListener);
      return;
    }
    this.openListeners.add(listener as OpenListener);
  }

  close(code = 1000, reason = ""): void {
    this.readyState = FakeWebSocket.CLOSED;
    this.emitClose(code, reason);
  }

  emitOpen(): void {
    this.readyState = FakeWebSocket.OPEN;
    for (const listener of this.openListeners) {
      listener();
    }
  }

  emitMessage(payload: unknown): void {
    const data = JSON.stringify(payload);
    for (const listener of this.messageListeners) {
      listener({ data });
    }
  }

  emitClose(code: number, reason = ""): void {
    this.readyState = FakeWebSocket.CLOSED;
    for (const listener of this.closeListeners) {
      listener({ code, reason });
    }
  }
}

function flushPromises(): Promise<void> {
  return Promise.resolve();
}

describe("useLayerRealtime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    vi.resetModules();
    FakeWebSocket.reset();
    vi.stubGlobal("WebSocket", FakeWebSocket);
  });

  it("connects to the active layer and routes incoming feature events", async () => {
    const onFeatureCreated = vi.fn();
    const onFeatureUpdated = vi.fn();
    const onFeatureDeleted = vi.fn();
    const { useLayerRealtime } =
      await import("@/composables/map/useLayerRealtime");
    const realtime = useLayerRealtime({
      onFeatureCreated,
      onFeatureUpdated,
      onFeatureDeleted,
    });

    await realtime.connectToLayer("layer-1", "token-1");

    const socket = FakeWebSocket.instances[0];
    expect(socket.url).toContain("/api/v1/ws/layers/layer-1");
    expect(socket.url).toContain("token=token-1");

    socket.emitOpen();
    socket.emitMessage({ type: "connected", layerId: "layer-1" });

    const feature = {
      type: "Feature",
      id: "feature-1",
      version: 1,
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [10, 10],
            [11, 10],
            [11, 11],
            [10, 10],
          ],
        ],
      },
      properties: { name: "Feature 1" },
    };

    socket.emitMessage({
      type: "feature_created",
      eventId: "evt_created",
      occurredAt: "2026-04-14T10:20:30Z",
      layerId: "layer-1",
      feature,
    });
    socket.emitMessage({
      type: "feature_updated",
      eventId: "evt_updated",
      occurredAt: "2026-04-14T10:20:31Z",
      layerId: "layer-1",
      feature,
    });
    socket.emitMessage({
      type: "feature_deleted",
      eventId: "evt_deleted",
      occurredAt: "2026-04-14T10:20:32Z",
      layerId: "layer-1",
      featureId: "feature-1",
    });

    await flushPromises();

    expect(realtime.isConnected.value).toBe(true);
    expect(onFeatureCreated).toHaveBeenCalledWith("layer-1", feature);
    expect(onFeatureUpdated).toHaveBeenCalledWith("layer-1", feature);
    expect(onFeatureDeleted).toHaveBeenCalledWith("layer-1", "feature-1");
  });

  it("reconnects after transport close and syncs only after reconnect", async () => {
    const onReconnectSynced = vi.fn();
    const { useLayerRealtime } =
      await import("@/composables/map/useLayerRealtime");
    const realtime = useLayerRealtime({
      onReconnectSynced,
    });

    await realtime.connectToLayer("layer-1", "token-1");
    const firstSocket = FakeWebSocket.instances[0];
    firstSocket.emitOpen();
    firstSocket.emitMessage({ type: "connected", layerId: "layer-1" });
    await flushPromises();

    expect(onReconnectSynced).not.toHaveBeenCalled();

    firstSocket.emitClose(1006);
    expect(realtime.isReconnecting.value).toBe(true);

    await vi.advanceTimersByTimeAsync(500);

    const secondSocket = FakeWebSocket.instances[1];
    secondSocket.emitOpen();
    secondSocket.emitMessage({ type: "connected", layerId: "layer-1" });
    await flushPromises();

    expect(onReconnectSynced).toHaveBeenCalledWith("layer-1");
    expect(realtime.isConnected.value).toBe(true);
    expect(realtime.isReconnecting.value).toBe(false);
  });

  it("does not reconnect after intentional disconnect", async () => {
    const { useLayerRealtime } =
      await import("@/composables/map/useLayerRealtime");
    const realtime = useLayerRealtime();

    await realtime.connectToLayer("layer-1", "token-1");
    const socket = FakeWebSocket.instances[0];
    socket.emitOpen();
    socket.emitMessage({ type: "connected", layerId: "layer-1" });

    realtime.disconnect();
    await vi.runAllTimersAsync();

    expect(realtime.isReconnecting.value).toBe(false);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("stops reconnect after hitting the retry limit", async () => {
    const { REALTIME_RECONNECT_DELAYS_MS, useLayerRealtime } =
      await import("@/composables/map/useLayerRealtime");
    const realtime = useLayerRealtime();

    await realtime.connectToLayer("layer-1", "token-1");
    FakeWebSocket.instances[0].emitOpen();
    FakeWebSocket.instances[0].emitMessage({
      type: "connected",
      layerId: "layer-1",
    });

    for (const delay of REALTIME_RECONNECT_DELAYS_MS) {
      const currentSocket = FakeWebSocket.instances.at(-1);
      currentSocket?.emitClose(1006);
      await vi.advanceTimersByTimeAsync(delay);
      FakeWebSocket.instances.at(-1)?.emitOpen();
    }

    FakeWebSocket.instances.at(-1)?.emitClose(1006);
    await vi.runAllTimersAsync();

    expect(realtime.hasStoppedReconnect.value).toBe(true);
    expect(realtime.isReconnecting.value).toBe(false);
  });

  it("stops reconnect on auth-related websocket close", async () => {
    const { useLayerRealtime } =
      await import("@/composables/map/useLayerRealtime");
    const realtime = useLayerRealtime();

    await realtime.connectToLayer("layer-1", "token-1");
    const socket = FakeWebSocket.instances[0];
    socket.emitOpen();
    socket.emitClose(1008);
    await vi.runAllTimersAsync();

    expect(realtime.isAuthError.value).toBe(true);
    expect(realtime.hasStoppedReconnect.value).toBe(true);
    expect(realtime.isReconnecting.value).toBe(false);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });
});
