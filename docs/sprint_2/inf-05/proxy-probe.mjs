import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createServer } from "node:http";

const sha = (body) => createHash("sha256").update(body).digest("hex");

// Диагностический upstream: только транспорт, без заявления о доменном Save.
if (process.argv.includes("--server")) {
  createServer(async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        method: req.method,
        uri: req.url,
        bytes: body.length,
        sha256: sha(body),
      }),
    );
  }).listen(8000, "0.0.0.0");
}

export async function checkProxy(origin, geometryPath) {
  const large = Buffer.alloc(1_048_577, 0x61);
  const small = Buffer.from("small control");
  const cases = [
    [geometryPath, large, 200],
    [`${geometryPath}?probe=1`, large, 200],
    ["/api/v1/auth/login", large, 413],
    [`${geometryPath}/extra`, large, 413],
    [`${geometryPath}-extra`, large, 413],
    ["/api/v1/auth/login", small, 200],
    [geometryPath, small, 200],
  ];
  const results = [];
  for (const [uri, body, expected] of cases) {
    const response = await fetch(origin + uri, {
      method: "PUT",
      body,
      signal: AbortSignal.timeout(15_000),
    });
    const text = await response.text();
    const row = { uri, bytes: body.length, status: response.status, expected };
    results.push(row);
    if (response.status === 200) {
      assert.deepEqual(JSON.parse(text), {
        method: "PUT",
        uri,
        bytes: body.length,
        sha256: sha(body),
      });
      row.bodyIntact = true;
    }
  }
  return { passed: results.every((r) => r.status === r.expected), results };
}
