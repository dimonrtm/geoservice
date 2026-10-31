// Сигналы и удерживаемые route responses принадлежат одному сценарию.
export async function withAcceptanceSignals(
  action,
  { timeoutMs = 15000 } = {},
) {
  const releases = [];
  const deferred = () => {
    let resolve;
    const promise = new Promise((done) => {
      resolve = done;
    });
    return { promise, resolve };
  };
  const signal = () => {
    const pending = deferred();
    return {
      resolve: pending.resolve,
      wait: async () => {
        let timer;
        try {
          return await Promise.race([
            pending.promise,
            new Promise((_, reject) => {
              timer = setTimeout(() => {
                const error = new Error(
                  "Истёк срок ожидания сигнала browser acceptance",
                );
                error.safeMessage = error.message;
                reject(error);
              }, timeoutMs);
            }),
          ]);
        } finally {
          clearTimeout(timer);
        }
      },
    };
  };
  const barrier = () => {
    const pending = deferred();
    releases.push(pending.resolve);
    return pending;
  };
  try {
    return await action({ signal, barrier });
  } finally {
    for (const release of releases) release();
  }
}

// Общий жизненный цикл browser evidence; browser actions остаются в smoke.mjs.
export async function recordAcceptanceResult(
  result,
  execute,
  { close, persist, scope = "all" },
) {
  let aborted = false;
  let failure;
  try {
    await execute();
  } catch (error) {
    aborted = true;
    failure = error;
  }
  try {
    await close();
  } catch (error) {
    if (!aborted) failure = error;
    aborted = true;
  }
  result.finishedAt = new Date().toISOString();
  result.scope = scope;
  result.completed = !aborted;
  result.aborted = aborted;
  result.passed =
    !aborted &&
    Object.keys(result.cases).length > 0 &&
    Object.values(result.cases).every((entry) => entry.passed);
  if (aborted) Object.assign(result, failedAcceptanceResult(result));
  try {
    await persist(result);
  } catch (error) {
    Object.assign(result, failedAcceptanceResult(result));
    // Если первая запись успела сохранить success перед ошибкой, заменяем её.
    // При постоянном отказе FS вызывающий harness также принудительно ставит failed.
    try {
      await persist(result);
    } catch {
      // Исходное исключение остаётся причиной failed, raw output не сохраняется.
    }
    throw aborted ? failure : error;
  }
  if (aborted) throw failure;
}

export function failedAcceptanceResult(previous) {
  return {
    ...previous,
    passed: false,
    completed: false,
    aborted: true,
    failure: "Аварийное завершение browser acceptance; gate не закрыт",
  };
}
