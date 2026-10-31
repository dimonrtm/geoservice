import { nextTick, shallowRef, type Ref } from "vue";
import { Map, NavigationControl, type StyleSpecification } from "maplibre-gl";
import { baseMapStyle } from "@/composables/map/mapStyle";

export function useMapInstance(
  mapEl: Ref<HTMLDivElement | null>,
  style: StyleSpecification = baseMapStyle,
) {
  const map = shallowRef<Map | null>(null);
  let cancelStartup: (() => void) | null = null;

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

    return new Promise<Map | null>((resolve, reject) => {
      let cancelled = false;
      const isActive = () => !cancelled && map.value === nextMap;
      const fail = (error: unknown) => {
        if (!isActive()) return;
        cancelled = true;
        nextMap.off("load", onLoad);
        reject(error);
      };
      const onLoad = async () => {
        if (!isActive()) return;
        nextMap.off("load", onLoad);
        try {
          await nextTick();
          if (!isActive()) return;
          nextMap.resize();
          resolve(nextMap);
        } catch (error) {
          fail(error);
        }
      };
      cancelStartup = () => {
        if (!cancelled) {
          cancelled = true;
          nextMap.off("load", onLoad);
        }
        resolve(null);
      };
      nextMap.on("load", onLoad);
      void (async () => {
        try {
          await nextTick();
          if (isActive()) nextMap.resize();
        } catch (error) {
          fail(error);
        }
      })();
    });
  }

  function destroyMap(): void {
    cancelStartup?.();
    cancelStartup = null;
    map.value?.remove();
    map.value = null;
  }

  return {
    map,
    createMap,
    destroyMap,
  };
}
