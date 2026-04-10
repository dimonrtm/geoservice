import { nextTick, shallowRef, type Ref } from "vue";
import { Map, NavigationControl, type StyleSpecification } from "maplibre-gl";
import { baseMapStyle } from "@/composables/map/mapStyle";

export function useMapInstance(
  mapEl: Ref<HTMLDivElement | null>,
  style: StyleSpecification = baseMapStyle,
) {
  const map = shallowRef<Map | null>(null);

  async function createMap(): Promise<Map | null> {
    if (!mapEl.value) {
      return null;
    }

    const nextMap = new Map({
      container: mapEl.value,
      style,
      center: [70.1902, 52.937],
      zoom: 8,
    });

    nextMap.addControl(new NavigationControl(), "top-right");
    map.value = nextMap;

    await nextTick();
    nextMap.resize();

    await new Promise<void>((resolve) => {
      nextMap.once("load", async () => {
        await nextTick();
        nextMap.resize();
        resolve();
      });
    });

    return nextMap;
  }

  function destroyMap(): void {
    map.value?.remove();
    map.value = null;
  }

  return {
    map,
    createMap,
    destroyMap,
  };
}
