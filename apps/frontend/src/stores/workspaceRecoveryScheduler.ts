type Job = { key: string; signal: AbortSignal; start(): void; cancel(): void };
export function createRecoveryScheduler(limit: number) {
  const active = new Set<string>(),
    queue: Job[] = [];
  function drain() {
    while (active.size < limit) {
      const index = queue.findIndex((job) => !active.has(job.key));
      if (index < 0) return;
      const job = queue.splice(index, 1)[0]!;
      if (job.signal.aborted) {
        job.cancel();
        continue;
      }
      active.add(job.key);
      job.start();
    }
  }
  return {
    run<T>(
      key: string,
      signal: AbortSignal,
      request: () => Promise<T>,
    ): Promise<T> {
      return new Promise<T>((resolve, reject) => {
        const cancel = () => {
          const index = queue.indexOf(job);
          if (index >= 0) queue.splice(index, 1);
          signal.removeEventListener("abort", cancel);
          reject(new Error("Recovery cancelled"));
        };
        const job: Job = {
          key,
          signal,
          cancel,
          start() {
            signal.removeEventListener("abort", cancel);
            void Promise.resolve()
              .then(() => {
                if (signal.aborted) throw new Error("Recovery cancelled");
                return request();
              })
              .then(resolve, reject)
              .finally(() => {
                active.delete(key);
                drain();
              });
          },
        };
        if (signal.aborted) {
          cancel();
          return;
        }
        signal.addEventListener("abort", cancel, { once: true });
        queue.push(job);
        drain();
      });
    },
  };
}
