import { isApiFeature } from "@/contracts/api";
import { isRecord, isString } from "@/contracts/geojson";
import type { ApiFeature } from "@/contracts/geojson";

export type RealtimeConnectedEvent = {
  type: "connected";
  layerId: string;
};

export type FeatureCreatedEvent = {
  type: "feature_created";
  eventId: string;
  occurredAt: string;
  layerId: string;
  feature: ApiFeature;
};

export type FeatureUpdatedEvent = {
  type: "feature_updated";
  eventId: string;
  occurredAt: string;
  layerId: string;
  feature: ApiFeature;
};

export type FeatureDeletedEvent = {
  type: "feature_deleted";
  eventId: string;
  occurredAt: string;
  layerId: string;
  featureId: string;
};

export type LayerRealtimeEvent =
  | RealtimeConnectedEvent
  | FeatureCreatedEvent
  | FeatureUpdatedEvent
  | FeatureDeletedEvent;

export function parseLayerRealtimeEvent(
  raw: string | unknown,
): LayerRealtimeEvent | null {
  if (typeof raw === "string") {
    try {
      const parsed = JSON.parse(raw) as unknown;
      return isLayerRealtimeEvent(parsed) ? parsed : null;
    } catch {
      return null;
    }
  }

  return isLayerRealtimeEvent(raw) ? raw : null;
}

export function isLayerRealtimeEvent(raw: unknown): raw is LayerRealtimeEvent {
  if (!isRecord(raw) || !isString(raw.type)) {
    return false;
  }

  switch (raw.type) {
    case "connected":
      return isConnectedEvent(raw);
    case "feature_created":
      return isFeatureCreatedEvent(raw);
    case "feature_updated":
      return isFeatureUpdatedEvent(raw);
    case "feature_deleted":
      return isFeatureDeletedEvent(raw);
    default:
      return false;
  }
}

function hasBaseFeatureRealtimeFields(raw: unknown): raw is {
  eventId: string;
  occurredAt: string;
  layerId: string;
} {
  return (
    isRecord(raw) &&
    isString(raw.eventId) &&
    isString(raw.occurredAt) &&
    isString(raw.layerId)
  );
}

function isConnectedEvent(raw: unknown): raw is RealtimeConnectedEvent {
  return isRecord(raw) && raw.type === "connected" && isString(raw.layerId);
}

function isFeatureCreatedEvent(raw: unknown): raw is FeatureCreatedEvent {
  return (
    isRecord(raw) &&
    raw.type === "feature_created" &&
    hasBaseFeatureRealtimeFields(raw) &&
    isApiFeature(raw.feature)
  );
}

function isFeatureUpdatedEvent(raw: unknown): raw is FeatureUpdatedEvent {
  return (
    isRecord(raw) &&
    raw.type === "feature_updated" &&
    hasBaseFeatureRealtimeFields(raw) &&
    isApiFeature(raw.feature)
  );
}

function isFeatureDeletedEvent(raw: unknown): raw is FeatureDeletedEvent {
  return (
    isRecord(raw) &&
    raw.type === "feature_deleted" &&
    hasBaseFeatureRealtimeFields(raw) &&
    isString(raw.featureId)
  );
}
