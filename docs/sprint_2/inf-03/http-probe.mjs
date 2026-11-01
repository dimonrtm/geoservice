export async function readHttpResponse(url, timeout) {
  const controller = new AbortController();
  let timer;
  // AbortSignal.timeout использует unref-таймер: он не удерживает standalone
  // Node-процесс до завершения fetch/body. Здесь deadline удерживает event loop
  // и отклоняет ожидание даже если транспорт не завершится после abort.
  const deadline = new Promise((_, reject) => {
    timer = setTimeout(() => {
      const error = new DOMException(
        `HTTP: таймаут ${timeout} мс`,
        "TimeoutError",
      );
      controller.abort(error);
      reject(error);
    }, timeout);
  });
  try {
    return await Promise.race([
      (async () => {
        const response = await fetch(url, { signal: controller.signal });
        return { status: response.status, text: await response.text() };
      })(),
      deadline,
    ]);
  } finally {
    clearTimeout(timer);
  }
}
