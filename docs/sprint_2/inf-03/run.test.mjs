import assert from "node:assert/strict";
import { test } from "node:test";
import { runCommand } from "./run.mjs";
import { readHttpResponse } from "./http-probe.mjs";
import { createServer } from "node:http";
import { once } from "node:events";

test("запускает процесс без shell и возвращает stdout", async () => {
  assert.equal(
    await runCommand(process.execPath, [
      "-e",
      "process.stdout.write(process.argv[1])",
      "literal $value & text",
    ]),
    "literal $value & text",
  );
});

test("ошибка spawn и nonzero не превращаются в успех", async () => {
  await assert.rejects(runCommand("inf03-nonexistent-command", []), /ENOENT/);
  await assert.rejects(
    runCommand(process.execPath, ["-e", "process.exit(7)"]),
    /код 7/,
  );
});

test("таймаут завершает собственный процесс", async () => {
  const start = Date.now();
  await assert.rejects(
    runCommand(process.execPath, ["-e", "setInterval(() => {}, 1000)"], 100),
    /таймаут/,
  );
  assert.ok(Date.now() - start < 10000);
});

test("таймаут завершает также потомка с унаследованным stdout", async () => {
  const script = `require('node:child_process').spawn(process.execPath, ['-e', 'setTimeout(() => {}, 4000)'], {stdio:'inherit'}); setInterval(() => {}, 1000);`;
  const start = Date.now();
  await assert.rejects(
    runCommand(process.execPath, ["-e", script], 500),
    /таймаут/,
  );
  assert.ok(
    Date.now() - start < 2500,
    "Потомок удерживает stdout после таймаута родителя",
  );
});

for (const phase of ["headers", "body"]) {
  test(`HTTP ${phase}: отдельный процесс дожидается unref-операции вместо exit 13`, async () => {
    const moduleUrl = new URL("./http-probe.mjs", import.meta.url).href;
    const script = `
      import { readHttpResponse } from ${JSON.stringify(moduleUrl)};
      const later = value => new Promise(resolve => setTimeout(() => resolve(value), 50).unref());
      globalThis.fetch = async () => ${phase === "headers" ? 'later({status:200,text:async()=>"ready"})' : '({status:200,text:()=>later("ready")})'};
      const result = await readHttpResponse('http://127.0.0.1/', 5000);
      console.log(JSON.stringify(result));
    `;
    assert.deepEqual(
      JSON.parse(
        await runCommand(
          process.execPath,
          ["--input-type=module", "-e", script],
          3000,
        ),
      ),
      { status: 200, text: "ready" },
    );
  });
}

test("HTTP: зависшее тело без handles завершается таймаутом и выполняет finally", async () => {
  const moduleUrl = new URL("./http-probe.mjs", import.meta.url).href;
  const script = `
    import { readHttpResponse } from ${JSON.stringify(moduleUrl)};
    let signal;
    globalThis.fetch = async (_url, options) => {
      signal = options.signal;
      return {status:200,text:()=>new Promise(()=>{})};
    };
    try { await readHttpResponse('http://127.0.0.1/', 50); process.exitCode=2; }
    catch(error) { console.log(error.name, signal.aborted); }
    finally { console.log('cleanup'); }
  `;
  const output = await runCommand(
    process.execPath,
    ["--input-type=module", "-e", script],
    3000,
  );
  assert.match(output, /TimeoutError true/);
  assert.match(output, /cleanup/);
});

test("HTTP: читает реальный ответ и ограничивает ожидание тела", async () => {
  const server = createServer((request, response) => {
    if (request.url === "/stalled") {
      response.writeHead(200);
      response.write("начало");
    } else {
      response.writeHead(503);
      response.end("ещё не готов");
    }
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const url = `http://127.0.0.1:${server.address().port}`;
  try {
    assert.deepEqual(await readHttpResponse(url, 1000), {
      status: 503,
      text: "ещё не готов",
    });
    await assert.rejects(readHttpResponse(`${url}/stalled`, 100), {
      name: "TimeoutError",
    });
  } finally {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
});
