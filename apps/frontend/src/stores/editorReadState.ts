import { shallowRef, ref } from "vue";
import { waitForRetry, AUTO_RETRY_DELAYS_MS } from "./workspaceRetry";
import { isAxiosError } from "axios";
export function createEditorReadState<T>() {
  const data = shallowRef<T | null>(null);
  const phase = ref<"idle" | "loading" | "ready" | "error">("idle");
  const error = shallowRef<unknown>(null);
  let controller: AbortController | null = null;
  function reset() {
    controller?.abort();
    controller = null;
    data.value = null;
    error.value = null;
    phase.value = "idle";
  }
  function accept(value: T) {
    reset();
    data.value = value;
    phase.value = "ready";
  }
  async function load(
    fetch: (signal: AbortSignal) => Promise<T>,
    retry: boolean,
    keepPrevious = false,
  ): Promise<T | null> {
    controller?.abort();
    if (!keepPrevious) data.value = null;
    error.value = null;
    const run = new AbortController();
    controller = run;
    phase.value = "loading";
    for (const delay of retry ? AUTO_RETRY_DELAYS_MS : [0]) {
      if (!(await waitForRetry(delay, run.signal))) return null;
      try {
        const value = await fetch(run.signal);
        if (run.signal.aborted) return null;
        data.value = value;
        phase.value = "ready";
        error.value = null;
        return value;
      } catch (cause) {
        if (run.signal.aborted) return null;
        error.value = cause;
        const status = isAxiosError(cause) ? cause.response?.status : undefined;
        if (
          status === 401 ||
          status === 403 ||
          status === 404 ||
          status === 409 ||
          (!retry && !(keepPrevious && data.value !== null))
        ) {
          phase.value = "error";
          throw cause;
        }
      }
    }
    phase.value = "error";
    return null;
  }
  return { data, phase, error, reset, accept, load };
}
