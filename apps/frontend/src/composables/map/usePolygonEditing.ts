import { watch, type Ref, type ShallowRef, type WatchStopHandle } from "vue";
import type {
  Map,
  MapGeoJSONFeature,
  MapLayerMouseEvent,
  MapMouseEvent,
} from "maplibre-gl";
import type { LayerDto } from "@/contracts/api";
import {
  isFiniteNumber,
  isRecord,
  isPolygonGeometry,
  toFiniteNumber,
  type ApiFeature,
  type PolygonGeometry,
} from "@/contracts/geojson";
import {
  ensureEditLayer,
  ensureEditSource,
  renderEditOverlay,
} from "@/map/maplibrelayers";
import {
  findNearestRingIndex,
  insertVertexOnNearestSegment,
  movePolygonVertex,
  removePolygonVertex,
} from "@/map/polygon-editing";
import { useEditStore } from "@/stores/edit";

export function usePolygonEditing(
  map: ShallowRef<Map | null>,
  activeLayer: Ref<LayerDto | null>,
) {
  const editStore = useEditStore();
  let overlayWatchStop: WatchStopHandle | null = null;
  let dragging = false;
  let dragRing = 0;
  let dragIndex = 0;

  function enableEditingOverlaySync(): void {
    disableEditingOverlaySync();

    const currentMap = map.value;
    if (!currentMap) {
      return;
    }

    ensureEditSource(currentMap);
    ensureEditLayer(currentMap);
    currentMap.on("mousedown", "edit:vertices:point", onVertexDown);
    currentMap.on("contextmenu", "edit:vertices:point", onVertexDelete);
    currentMap.on("click", "edit:polygon:outline", onOutlineInsert);
    renderEditOverlay(currentMap, editStore.edit);

    overlayWatchStop = watch(
      [() => editStore.edit, () => map.value],
      ([nextEditState, nextMap]) => {
        if (!nextMap) {
          return;
        }
        renderEditOverlay(nextMap, nextEditState);
      },
    );
  }

  function disableEditingOverlaySync(): void {
    overlayWatchStop?.();
    overlayWatchStop = null;

    const currentMap = map.value;
    if (!currentMap) {
      dragging = false;
      return;
    }

    currentMap.off("mousedown", "edit:vertices:point", onVertexDown);
    currentMap.off("contextmenu", "edit:vertices:point", onVertexDelete);
    currentMap.off("click", "edit:polygon:outline", onOutlineInsert);
    resetInteractionState();
  }

  function bindActiveLayerClick(layerId: string): void {
    map.value?.on("click", `layer:${layerId}`, onLayerClick);
  }

  function unbindActiveLayerClick(layerId: string | null | undefined): void {
    if (!layerId) {
      return;
    }
    map.value?.off("click", `layer:${layerId}`, onLayerClick);
  }

  function resetInteractionState(): void {
    dragging = false;
    const currentMap = map.value;
    if (!currentMap) {
      return;
    }
    currentMap.off("mousemove", onVertexMove);
    currentMap.dragPan.enable();
  }

  async function saveChange(): Promise<ApiFeature<PolygonGeometry> | null> {
    return await editStore.saveEditing();
  }

  async function deleteEditingFeature(): Promise<string | null> {
    return await editStore.deleteEditing();
  }

  function cancelEditing(): void {
    editStore.cancelEditing();
  }

  function onLayerClick(e: MapLayerMouseEvent): void {
    if (editStore.edit.mode === "editing" && editStore.edit.dirty) {
      return;
    }
    if (!e.features?.length) {
      return;
    }

    const feature = e.features[0];
    if (!feature || !feature.properties || !feature.geometry) {
      return;
    }

    if (!isRecord(feature.properties)) {
      return;
    }
    const props = feature.properties;
    const featureId = typeof props["__id"] === "string" ? props["__id"] : null;
    if (!featureId) {
      return;
    }

    const versionValue = props["__version"];
    const version = isFiniteNumber(versionValue) ? versionValue : null;
    if (version === null || !activeLayer.value) {
      return;
    }

    if (
      feature.geometry.type === "Polygon" &&
      isPolygonGeometry(feature.geometry)
    ) {
      editStore.startEditing({
        layerId: activeLayer.value.id,
        featureId,
        version,
        properties: props,
        geometry: feature.geometry,
      });
    }
  }

  function onVertexDown(e: MapLayerMouseEvent): void {
    if (!editStore.isEditing()) {
      return;
    }

    const currentMap = map.value;
    if (!currentMap) {
      return;
    }

    e.preventDefault();
    if (!e.features?.[0]) {
      return;
    }

    const ringAndVertexIndexies = parseRingAndVertexIndex(e.features[0]);
    if (!ringAndVertexIndexies) {
      return;
    }

    dragging = true;
    dragRing = ringAndVertexIndexies.ring;
    dragIndex = ringAndVertexIndexies.vertexIndex;
    currentMap.dragPan.disable();
    currentMap.on("mousemove", onVertexMove);
    currentMap.once("mouseup", onVertexUp);
  }

  function onVertexMove(e: MapMouseEvent): void {
    if (!dragging || !editStore.isEditing()) {
      return;
    }

    const session = editStore.sessionOrNull();
    if (!session) {
      return;
    }

    const nextGeometry = movePolygonVertex(
      session.draft.geometry,
      dragRing,
      dragIndex,
      e.lngLat.lng,
      e.lngLat.lat,
    );

    editStore.updateDraft({
      properties: session.draft.properties,
      geometry: nextGeometry,
    });
  }

  function onVertexUp(): void {
    resetInteractionState();
  }

  function onVertexDelete(e: MapLayerMouseEvent): void {
    if (!editStore.isEditing()) {
      return;
    }

    e.preventDefault();
    if (!e.features?.[0]) {
      return;
    }

    const ringAndVertexIndexies = parseRingAndVertexIndex(e.features[0]);
    if (!ringAndVertexIndexies) {
      return;
    }

    const session = editStore.sessionOrNull();
    if (!session) {
      return;
    }

    const editedPolygon = removePolygonVertex(
      session.draft.geometry,
      ringAndVertexIndexies.ring,
      ringAndVertexIndexies.vertexIndex,
    );
    if (!editedPolygon) {
      return;
    }

    editStore.updateDraft({
      properties: session.draft.properties,
      geometry: editedPolygon,
    });
  }

  function onOutlineInsert(e: MapLayerMouseEvent): void {
    if (!editStore.isEditing() || e.originalEvent.shiftKey !== true) {
      return;
    }

    e.preventDefault();
    const session = editStore.sessionOrNull();
    if (!session) {
      return;
    }

    const { lng, lat } = e.lngLat;
    const ringIndex = findNearestRingIndex(session.draft.geometry, lng, lat);
    if (ringIndex === null) {
      return;
    }

    const nextGeometry = insertVertexOnNearestSegment(
      session.draft.geometry,
      ringIndex,
      lng,
      lat,
    );
    if (!nextGeometry) {
      return;
    }

    editStore.updateDraft({
      properties: session.draft.properties,
      geometry: nextGeometry,
    });
  }

  return {
    editStore,
    enableEditingOverlaySync,
    disableEditingOverlaySync,
    bindActiveLayerClick,
    unbindActiveLayerClick,
    resetInteractionState,
    saveChange,
    deleteEditingFeature,
    cancelEditing,
  };
}

function parseRingAndVertexIndex(
  feature: MapGeoJSONFeature,
): { ring: number; vertexIndex: number } | null {
  if (
    feature.properties["ring"] === undefined ||
    feature.properties["i"] === undefined
  ) {
    return null;
  }

  const ring = toFiniteNumber(feature.properties["ring"]);
  const vertexIndex = toFiniteNumber(feature.properties["i"]);
  if (ring === null || vertexIndex === null) {
    return null;
  }

  return { ring, vertexIndex };
}
