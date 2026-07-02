import { ref } from "vue";
import { http } from "@/api/http";
import { requestLayerWebSocketTicket } from "@/api/realtime";
import {
  parseLayerRealtimeEvent,
  type FeatureCreatedEvent,
  type FeatureDeletedEvent,
  type FeatureUpdatedEvent,
} from "@/contracts/realtime";
import type { ApiFeature } from "@/contracts/geojson";
import type { LayerDto } from "@/contracts/api";

type RealtimeCallback = (layerId: string) => Promise<void> | void;
type FeatureCallback = (
  layerId: string,
  feature: ApiFeature,
) => Promise<void> | void;
type FeatureDeleteCallback = (
  layerId: string,
  featureId: string,
) => Promise<void> | void;

type UseLayerRealtimeOptions = {
  onFeatureCreated?: FeatureCallback;
  onFeatureUpdated?: FeatureCallback;
  onFeatureDeleted?: FeatureDeleteCallback;
  onReconnectSynced?: RealtimeCallback;
};

const REALTIME_RECONNECT_DELAYS_MS = [500, 1000, 2000, 5000] as const;
const TERMINAL_WEBSOCKET_CLOSE_CODE = 1008;

export function useLayerRealtime(options: UseLayerRealtimeOptions = {}) {
  const socket = ref<WebSocket | null>(null);
  const isConnected = ref(false);
  const isReconnecting = ref(false);
  const isSyncingAfterReconnect = ref(false);
  const hasStoppedReconnect = ref(false);
  const isAuthError = ref(false);
  const connectionError = ref<string | null>(null);

  const currentLayerId = ref<string | null>(null);
  const currentAuthReady = ref(false);

  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectAttempt = 0;
  let activeGeneration = 0;
  let intentionalCloseGeneration: number | null = null;

  async function connectToLayer(
    layerId: string,
    authReady = true,
  ): Promise<void> {
    currentAuthReady.value = authReady;
    if (!layerId || !authReady) {
      disconnect();
      return;
    }

    const sameConnectionRequested =
      currentLayerId.value === layerId &&
      socket.value !== null &&
      (socket.value.readyState === WebSocket.OPEN ||
        socket.value.readyState === WebSocket.CONNECTING);
    if (sameConnectionRequested) {
      return;
    }

    currentLayerId.value = layerId;
    reconnectAttempt = 0;
    clearReconnectTimer();
    await openSocket(layerId, false);
  }

  async function handleLayerChange(
    layer: LayerDto | null,
    authReady: boolean,
  ): Promise<void> {
    currentAuthReady.value = authReady;
    if (!layer || !authReady) {
      disconnect();
      return;
    }

    await connectToLayer(layer.id, authReady);
  }

  function disconnect(): void {
    clearReconnectTimer();
    activeGeneration += 1;
    isConnected.value = false;
    isReconnecting.value = false;
    isSyncingAfterReconnect.value = false;
    hasStoppedReconnect.value = false;
    isAuthError.value = false;
    connectionError.value = null;
    reconnectAttempt = 0;
    currentLayerId.value = null;
    currentAuthReady.value = false;

    if (socket.value) {
      intentionalCloseGeneration = activeGeneration;
      socket.value.close();
      socket.value = null;
    }
  }

  return {
    connectToLayer,
    disconnect,
    handleLayerChange,
    isConnected,
    isReconnecting,
    isSyncingAfterReconnect,
    hasStoppedReconnect,
    isAuthError,
    connectionError,
  };

  async function openSocket(layerId: string, isReconnect: boolean) {
    clearReconnectTimer();
    closeActiveSocketIfNeeded();

    activeGeneration += 1;
    const generation = activeGeneration;
    isConnected.value = false;
    isReconnecting.value = isReconnect;
    isSyncingAfterReconnect.value = false;
    hasStoppedReconnect.value = false;
    isAuthError.value = false;
    connectionError.value = null;

    let ticket: string;
    try {
      const issued = await requestLayerWebSocketTicket(layerId);
      ticket = issued.ticket;
    } catch {
      if (generation === activeGeneration) {
        isReconnecting.value = false;
        hasStoppedReconnect.value = true;
        isAuthError.value = true;
        connectionError.value = "Ошибка авторизации realtime";
      }
      return;
    }

    if (generation !== activeGeneration || currentLayerId.value !== layerId) {
      return;
    }

    const nextSocket = new WebSocket(buildLayerWebSocketUrl(layerId, ticket));
    socket.value = nextSocket;

    nextSocket.addEventListener("message", (event) => {
      if (generation !== activeGeneration) {
        return;
      }

      const parsed = parseLayerRealtimeEvent(event.data);
      if (!parsed || parsed.layerId !== currentLayerId.value) {
        return;
      }

      if (parsed.type === "connected") {
        void handleConnected(generation, layerId, isReconnect);
        return;
      }

      if (parsed.type === "feature_created") {
        void routeCreatedEvent(parsed);
        return;
      }

      if (parsed.type === "feature_updated") {
        void routeUpdatedEvent(parsed);
        return;
      }

      void routeDeletedEvent(parsed);
    });

    nextSocket.addEventListener("close", (event) => {
      if (generation !== activeGeneration) {
        return;
      }

      socket.value = null;
      isConnected.value = false;
      isSyncingAfterReconnect.value = false;

      if (intentionalCloseGeneration === generation) {
        intentionalCloseGeneration = null;
        isReconnecting.value = false;
        return;
      }

      if (event.code === TERMINAL_WEBSOCKET_CLOSE_CODE) {
        isReconnecting.value = false;
        hasStoppedReconnect.value = true;
        isAuthError.value = true;
        connectionError.value = "Ошибка авторизации realtime";
        return;
      }

      scheduleReconnect();
    });
  }

  async function handleConnected(
    generation: number,
    layerId: string,
    isReconnect: boolean,
  ): Promise<void> {
    if (generation !== activeGeneration) {
      return;
    }

    isConnected.value = true;
    isReconnecting.value = false;
    hasStoppedReconnect.value = false;
    isAuthError.value = false;
    connectionError.value = null;

    if (!isReconnect) {
      reconnectAttempt = 0;
      return;
    }

    reconnectAttempt = 0;
    isSyncingAfterReconnect.value = true;
    try {
      await options.onReconnectSynced?.(layerId);
    } finally {
      if (generation === activeGeneration) {
        isSyncingAfterReconnect.value = false;
      }
    }
  }

  function scheduleReconnect(): void {
    clearReconnectTimer();

    const nextLayerId = currentLayerId.value;
    if (!nextLayerId || !currentAuthReady.value) {
      isReconnecting.value = false;
      return;
    }

    if (reconnectAttempt >= REALTIME_RECONNECT_DELAYS_MS.length) {
      isReconnecting.value = false;
      hasStoppedReconnect.value = true;
      connectionError.value = "Переподключение realtime остановлено";
      return;
    }

    const delay = REALTIME_RECONNECT_DELAYS_MS[reconnectAttempt];
    reconnectAttempt += 1;
    isReconnecting.value = true;
    connectionError.value = null;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      void openSocket(nextLayerId, true);
    }, delay);
  }

  async function routeCreatedEvent(event: FeatureCreatedEvent): Promise<void> {
    await options.onFeatureCreated?.(event.layerId, event.feature);
  }

  async function routeUpdatedEvent(event: FeatureUpdatedEvent): Promise<void> {
    await options.onFeatureUpdated?.(event.layerId, event.feature);
  }

  async function routeDeletedEvent(event: FeatureDeletedEvent): Promise<void> {
    await options.onFeatureDeleted?.(event.layerId, event.featureId);
  }

  function closeActiveSocketIfNeeded(): void {
    if (!socket.value) {
      return;
    }

    intentionalCloseGeneration = activeGeneration;
    socket.value.close();
    socket.value = null;
  }

  function clearReconnectTimer(): void {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }
}

function buildLayerWebSocketUrl(layerId: string, ticket: string): string {
  const baseUrl = resolveWebSocketBaseUrl();
  const url = new URL(`/api/v1/ws/layers/${layerId}`, baseUrl);
  url.searchParams.set("ticket", ticket);
  return url.toString();
}

function resolveWebSocketBaseUrl(): string {
  const configuredBaseUrl =
    import.meta.env.VITE_API_BASE_URL ??
    http.defaults.baseURL ??
    "http://localhost:8000";

  if (
    configuredBaseUrl.startsWith("ws://") ||
    configuredBaseUrl.startsWith("wss://")
  ) {
    return configuredBaseUrl;
  }

  if (configuredBaseUrl.startsWith("http://")) {
    return `ws://${configuredBaseUrl.slice("http://".length)}`;
  }

  if (configuredBaseUrl.startsWith("https://")) {
    return `wss://${configuredBaseUrl.slice("https://".length)}`;
  }

  return "ws://localhost:8000";
}

export { REALTIME_RECONNECT_DELAYS_MS, TERMINAL_WEBSOCKET_CLOSE_CODE };
