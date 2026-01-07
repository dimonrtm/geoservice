<template>
  <!-- Контейнер под карту -->
  <div ref="mapEl" class="map"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";

const mapEl = ref<HTMLDivElement | null>(null);
let map: MapLibreMap | null = null;
const styleUrl = import.meta.env.VITE_MAP_STYLE_URL as string;
const emptyFeatureCollection: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [],
};
let isDestroyed = false;
let abortController: AbortController | null = null;
let moveTimer: ReturnType<typeof setTimeout> | null = null;
let requestSeq = 0;
let hoveredPointId: string | null = null;
let hoveredPolyId: string | null = null;
let interactionsBound = false;

onMounted(() => {
  if (!mapEl.value) return;
  isDestroyed = false;
  console.log("styleUrl:", styleUrl);
  map = new maplibregl.Map({
    container: mapEl.value,
    style: styleUrl,
    center: [76.8897, 43.2389],
    zoom: 10,
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");
  if (map.isStyleLoaded()) {
    onLoad();
  } else {
    map.on("load", onLoad);
  }

  map.on("error", (e) => {
    console.error("map error:", e.error);
  });
});

onBeforeUnmount(() => {
  isDestroyed = true;
  interactionsBound = false;
  abortController?.abort();
  map?.off("load", onLoad);
  map?.off("moveend", onMoveEnd);
  map?.off("mousemove", "points_unclustered", onPointsMove);
  map?.off("mouseleave", "points_unclustered", onPointsLeave);
  map?.off("click", "points_unclustered", onClick);
  map?.off("mousemove", "features_fill", onPolyMove);
  map?.off("mouseleave", "features_fill", onPolyLeave);
  map?.off("click", "features_fill", onClick);
  map?.off("click", "points_clusters", onClusterClick);
  map?.remove();
  map = null;
  console.log("map removed");
});

async function onLoad() {
  if (isDestroyed) {
    return;
  }
  initLayers();
  bindInteractions();
  await loadFeatures();
  map?.on("moveend", onMoveEnd);
}

function onMoveEnd() {
  if (moveTimer !== null) {
    clearTimeout(moveTimer);
  }
  moveTimer = setTimeout(() => {
    loadFeatures().catch(console.error);
  }, 250);
}

function initLayers() {
  if (isDestroyed) {
    return;
  }
  if (!map) {
    return;
  }
  const features = map.getSource("features");
  if (!features) {
    map.addSource("features", {
      type: "geojson",
      data: emptyFeatureCollection,
    });
  }
  const points = map.getSource("points");
  if (!points) {
    map.addSource("points", {
      type: "geojson",
      data: emptyFeatureCollection,
      cluster: true,
      clusterMaxZoom: 14,
      clusterRadius: 50,
    });
  }
  const fillLayer = map.getLayer("features_fill");
  if (!fillLayer) {
    map.addLayer({
      id: "features_fill",
      type: "fill",
      source: "features",
      filter: ["==", ["geometry-type"], "Polygon"],
      paint: {
        "fill-opacity": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          0.7,
          0.4,
        ],
        "fill-outline-color": "#000000",
      },
    });
  }
  const pointsLayer = map.getLayer("points_unclustered");
  if (pointsLayer) {
    map.moveLayer("points_unclustered");
  } else {
    map.addLayer({
      id: "points_unclustered",
      type: "circle",
      source: "points",
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3, 14, 8],
        "circle-opacity": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          1.0,
          0.8,
        ],
        "circle-stroke-width": [
          "case",
          ["boolean", ["feature-state", "hover"], false],
          3,
          1,
        ],
        "circle-stroke-color": "#000000",
      },
    });
  }
  const points_clusters = map.getLayer("points_clusters");
  if (points_clusters) {
    map.moveLayer("points_clusters", "points_unclustered");
  } else {
    map.addLayer(
      {
        id: "points_clusters",
        type: "circle",
        source: "points",
        filter: ["has", "point_count"],
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["get", "point_count"],
            10,
            12,
            100,
            20,
          ],
          "circle-opacity": 0.8,
        },
      },
      "points_unclustered",
    );
  }

  const outlineLayer = map.getLayer("features_outline");
  if (outlineLayer) {
    map.moveLayer("features_outline", "points_clusters");
  } else {
    map.addLayer(
      {
        id: "features_outline",
        type: "line",
        source: "features",
        filter: ["==", ["geometry-type"], "Polygon"],
        paint: {
          "line-color": "#000000",
          "line-width": ["interpolate", ["linear"], ["zoom"], 8, 1, 14, 3],
        },
      },
      "points_clusters",
    );
  }

  const pointCountAbbreviated = map.getLayer("cluster_count");
  if (pointCountAbbreviated) {
    map.moveLayer("cluster_count");
  } else {
    map.addLayer({
      id: "cluster_count",
      type: "symbol",
      source: "points",
      filter: ["has", "point_count"],
      layout: {
        "text-field": ["get", "point_count_abbreviated"],
        "text-size": 12,
      },
    });
  }
}

function bindInteractions() {
  if (!map || interactionsBound) {
    return;
  }
  map.on("mousemove", "points_unclustered", onPointsMove);
  map.on("mouseleave", "points_unclustered", onPointsLeave);
  map.on("click", "points_unclustered", onClick);
  map.on("mousemove", "features_fill", onPolyMove);
  map.on("mouseleave", "features_fill", onPolyLeave);
  map.on("click", "features_fill", onClick);
  map.on("click", "points_clusters", onClusterClick);
  map.on(
    "mouseenter",
    "points_clusters",
    () => (map!.getCanvas().style.cursor = "pointer"),
  );
  map.on(
    "mouseleave",
    "points_clusters",
    () => (map!.getCanvas().style.cursor = ""),
  );
  interactionsBound = true;
}

function updateFeatures(data: GeoJSON.FeatureCollection, source: string) {
  initLayers();
  const src = getGeoJsonSource(source);
  if (!src) {
    return;
  }
  const safe: GeoJSON.FeatureCollection = {
    type: "FeatureCollection",
    features: Array.isArray(data.features) ? data.features : [],
  };
  src.setData(safe);
}

async function loadFeatures(): Promise<void> {
  try {
    abortController?.abort();
    abortController = new AbortController();
    if (!map) {
      throw new Error("map is null");
    }
    const bounds = map.getBounds();
    const params = new URLSearchParams({
      minLon: String(bounds.getWest()),
      minLat: String(bounds.getSouth()),
      maxLon: String(bounds.getEast()),
      maxLat: String(bounds.getNorth()),
    }).toString();
    const seq = ++requestSeq;
    const res = await fetch("http://localhost:8000/api/features?" + params, {
      signal: abortController.signal,
    });
    if (!res?.ok) {
      throw Error(`HTTP ${res?.status}`);
    }
    const data: unknown = await res.json();
    if (
      typeof data !== "object" ||
      data === null ||
      !Array.isArray((data as any).points) ||
      !Array.isArray((data as any).polygons)
    ) {
      throw Error("Полигоны и точки должны приходить как массив объектов");
    }
    const raw: unknown[] = [...(data as any).points, ...(data as any).polygons];
    const valid = filterValidFeatures(raw);
    const validPointsFeatures = valid.filter(isPointFeature);
    const validPolygonFeatures = valid.filter(isPolygonFeature);
    const featurePolygonCollection: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: validPolygonFeatures,
    };
    const featurePointCollection: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: validPointsFeatures,
    };
    if (seq !== requestSeq) {
      return;
    }
    if (isDestroyed) {
      return;
    }
    updateFeatures(featurePolygonCollection, "features");
    updateFeatures(featurePointCollection, "points");
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw err;
    } else {
      console.error("Ошибка при загрузке Features", err);
      throw err;
    }
  }
}

function getGeoJsonSource(source: string): maplibregl.GeoJSONSource | null {
  if (!map) {
    return null;
  }
  const src = map.getSource(source) as maplibregl.GeoJSONSource | undefined;
  return src ?? null;
}

function filterValidFeatures(features: unknown[]): GeoJSON.Feature[] {
  const resultFeatures: GeoJSON.Feature[] = [];
  for (const feature of features) {
    if (typeof feature !== "object" || feature === null) {
      continue;
    }
    const checkFeature = feature as { type?: unknown; geometry?: unknown };
    if (checkFeature.type !== "Feature") {
      continue;
    }
    if (
      typeof checkFeature.geometry !== "object" ||
      checkFeature.geometry === null
    ) {
      continue;
    }
    const checkGeometry = checkFeature.geometry as { type?: unknown };
    if (checkGeometry.type !== "Point" && checkGeometry.type !== "Polygon") {
      continue;
    }
    resultFeatures.push(feature as GeoJSON.Feature);
  }
  return resultFeatures;
}

/*function clearFeatures(): void{
  updateFeatures({type: "FeatureCollection", features: []}, "features");
  updateFeatures({type: "FeatureCollection", features: []}, "points");
}*/

function onPointsMove(e: maplibregl.MapLayerMouseEvent): void {
  if (!map) {
    return;
  }
  const feature = e.features?.[0];
  if (!feature || feature == null) {
    return;
  }
  const featureId = String(feature.id);
  if (hoveredPointId && hoveredPointId !== featureId) {
    map.setFeatureState(
      { source: "points", id: hoveredPointId },
      { hover: false },
    );
  }
  hoveredPointId = featureId;
  map.setFeatureState({ source: "points", id: featureId }, { hover: true });
}

function onPointsLeave(): void {
  if (!map) {
    return;
  }
  if (hoveredPointId) {
    map.setFeatureState(
      { source: "points", id: hoveredPointId },
      { hover: false },
    );
    hoveredPointId = null;
  }
}

function onClick(e: maplibregl.MapLayerMouseEvent): void {
  if (!map) {
    return;
  }
  const feature = e.features?.[0];
  if (!feature) {
    return;
  }
  const properties = (feature.properties ?? {}) as Record<string, any>;
  const name = String(properties.name ?? "not name");
  new maplibregl.Popup().setLngLat(e.lngLat).setText(name).addTo(map!);
}

function onClusterClick(e: maplibregl.MapLayerMouseEvent): void {
  if (!map) {
    return;
  }
  const feature = e.features?.[0];
  if (!feature) {
    return;
  }
  const coords = (feature.geometry as any).coordinates as [number, number];
  map.easeTo({ center: coords, zoom: map.getZoom() + 2 });
}

function onPolyMove(e: maplibregl.MapLayerMouseEvent): void {
  if (!map) {
    return;
  }
  map.getCanvas().style.cursor = "pointer";
  const feature = e.features?.[0];
  if (!feature || feature == null) {
    return;
  }
  const featureId = String(feature.id);
  if (hoveredPolyId && hoveredPolyId !== featureId) {
    map.setFeatureState(
      { source: "features", id: hoveredPolyId },
      { hover: false },
    );
  }
  hoveredPolyId = featureId;
  map.setFeatureState({ source: "features", id: featureId }, { hover: true });
}

function onPolyLeave(): void {
  if (!map) {
    return;
  }
  map.getCanvas().style.cursor = "";
  if (hoveredPolyId) {
    map.setFeatureState(
      { source: "features", id: hoveredPolyId },
      { hover: false },
    );
    hoveredPolyId = null;
  }
}

function isPointFeature(feature: GeoJSON.Feature) {
  return feature.geometry.type == "Point";
}

function isPolygonFeature(feature: GeoJSON.Feature) {
  return feature.geometry.type == "Polygon";
}
</script>

<style scoped>
/* ВАЖНО: если высоты нет — карта будет “невидимой” */
.map {
  width: 100%;
  height: 100vh;
}
</style>
