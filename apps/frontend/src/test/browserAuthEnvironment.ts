/** Последовательный Web Locks port для тестов store/API; секреты не сохраняются. */
export function installBrowserAuthEnvironment(): void {
  localStorage.clear();
  let tail = Promise.resolve();
  Object.defineProperty(navigator, "locks", {
    configurable: true,
    value: {
      async request<T>(
        _name: string,
        options: { signal: AbortSignal },
        action: () => Promise<T>,
      ) {
        const previous = tail;
        let release!: () => void;
        tail = previous.then(
          () =>
            new Promise<void>((resolve) => {
              release = resolve;
            }),
        );
        await previous;
        try {
          options.signal.throwIfAborted();
          return await action();
        } finally {
          release();
        }
      },
    },
  });
}
