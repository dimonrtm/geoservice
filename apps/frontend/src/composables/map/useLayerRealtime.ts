import { ref } from "vue";
import { http } from "@/api/http";
import { getApiBaseUrl, layerWebSocketUrl } from "@/api/baseUrl";
import { requestLayerWebSocketTicket } from "@/api/realtime";
import {
  parseLayerRealtimeEvent,
  type FeatureCreatedEvent,
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
  deletedVersion: number,
) => Promise<void> | void;

type UseLayerRealtimeOptions = {
  onFeatureCreated?: FeatureCallback;
  onFeatureUpdated?: FeatureCallback;
  onFeatureDeleted?: FeatureDeleteCallback;
  onSubscriptionEnded?: (layerId: string) => void;
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
    if (currentLayerId.value)
      options.onSubscriptionEnded?.(currentLayerId.value);
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
    restartSubscription: () => socket.value?.close(),
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
    } catch (error) {
      if (generation === activeGeneration) {
        if (!isTerminalError(error)) {
          scheduleReconnect();
          return;
        }
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
        void handleConnected(generation, layerId);
        return;
      }

      const recover = () => {
        if (generation === activeGeneration) nextSocket.close();
      };
      if (parsed.type === "feature_created") {
        void routeCreatedEvent(parsed).catch(recover);
        return;
      }

      if (parsed.type === "feature_updated") {
        void routeUpdatedEvent(parsed).catch(recover);
        return;
      }

      if (parsed.deletedVersion === undefined) {
        recover();
        return;
      }
      void Promise.resolve()
        .then(() => {
          if (generation === activeGeneration)
            return options.onFeatureDeleted?.(
              parsed.layerId,
              parsed.featureId,
              parsed.deletedVersion!,
            );
        })
        .catch(recover);
    });

    nextSocket.addEventListener("close", (event) => {
      if (generation !== activeGeneration) {
        return;
      }

      activeGeneration += 1;
      options.onSubscriptionEnded?.(layerId);
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
  ): Promise<void> {
    if (generation !== activeGeneration) {
      return;
    }

    isConnected.value = true;
    isReconnecting.value = false;
    hasStoppedReconnect.value = false;
    isAuthError.value = false;
    connectionError.value = null;

    isSyncingAfterReconnect.value = true;
    try {
      await options.onReconnectSynced?.(layerId);
      if (generation === activeGeneration) reconnectAttempt = 0;
    } catch (error) {
      if (generation !== activeGeneration) return;
      if (isTerminalError(error)) {
        disconnect();
        isAuthError.value = true;
        hasStoppedReconnect.value = true;
      } else {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          if (generation === activeGeneration)
            void handleConnected(generation, layerId);
        }, retryDelay());
      }
    } finally {
      if (generation === activeGeneration && !reconnectTimer) {
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

    const delay = retryDelay();
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

  function retryDelay(): number {
    return (
      REALTIME_RECONNECT_DELAYS_MS[reconnectAttempt++] ??
      15000 + Math.floor(Math.random() * 15001)
    );
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

function isTerminalError(error: unknown) {
  if (!error || typeof error !== "object") return false;
  const failure = error as { status?: number; response?: { status?: number } };
  return [401, 403, 404].includes(
    failure.response?.status ?? failure.status ?? 0,
  );
}

function buildLayerWebSocketUrl(layerId: string, ticket: string): string {
  return layerWebSocketUrl(
    http.defaults.baseURL ?? getApiBaseUrl(),
    layerId,
    ticket,
  );
}

export { REALTIME_RECONNECT_DELAYS_MS, TERMINAL_WEBSOCKET_CLOSE_CODE };
