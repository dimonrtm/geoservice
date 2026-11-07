import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";

// Настоящий API через production nginx. Не выдаётся за browser editing proof.
export async function checkLargeApi({ origin, fixture }) {
  let token;
  async function request(uri, method = "GET", body) {
    const response = await fetch(origin + uri, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });
    const result = await response.json();
    assert.ok(
      response.ok,
      `${method} ${uri}: ${response.status} ${result.code ?? ""}`,
    );
    return result;
  }
  token = (
    await request("/api/v1/auth/login", "POST", {
      email: "alexey.editor@example.local",
      password: "alexey-editor-password",
    })
  ).access_token;
  assert.equal(typeof token, "string");
  const root = `/api/v1/work-orders/${fixture.workOrderId}/edit-versions`;
  const opened = await request(root, "POST");
  const versionPath = `${root}/${opened.editVersion.id}`;
  const geometryPath = `${root}/${opened.editVersion.id}/features/${fixture.featureId}/geometry`;
  const initial = await request(versionPath);
  const version = (w) => w.workOrder.editVersion;
  const current = (w) =>
    version(w).features.features.find((f) => f.id === fixture.featureId)
      .geometry;
  const baseline = current(initial);
  assert.deepEqual(baseline.coordinates, fixture.coordinates);
  const candidate = structuredClone(baseline);
  candidate.coordinates[1][1] = Number(
    (candidate.coordinates[1][1] + 0.0001).toFixed(7),
  );
  const commands = [];
  async function save(geometry, draftVersionToken) {
    const body = { commandId: randomUUID(), draftVersionToken, geometry };
    const bytes = Buffer.byteLength(JSON.stringify(body));
    assert.ok(bytes > 1_048_576, `Request too small: ${bytes}`);
    const result = await request(geometryPath, "PUT", body);
    assert.equal(result.commandId, body.commandId);
    assert.equal(result.commandState, "succeeded");
    commands.push({
      path: geometryPath,
      commandId: body.commandId,
      bytes,
      operation: result.operation,
    });
    return { body, result };
  }
  const saved = await save(candidate, version(initial).draftVersionToken);
  assert.equal(saved.result.operation, "updated");
  assert.equal(saved.result.hasPersistedChangeSet, true);
  const readback = await request(versionPath);
  assert.deepEqual(current(readback), saved.result.updatedFeature.geometry);
  assert.deepEqual(current(readback), candidate);
  assert.deepEqual(
    (await request(`${versionPath}/features/${fixture.featureId}/baseline`))
      .baselineGeometry,
    baseline,
  );
  assert.notEqual(
    version(readback).draftVersionToken,
    version(initial).draftVersionToken,
  );
  const replay = await request(geometryPath, "PUT", saved.body);
  assert.equal(replay.commandId, saved.body.commandId);
  assert.equal(replay.draftVersionToken, saved.result.draftVersionToken);
  const reverted = await save(baseline, version(readback).draftVersionToken);
  assert.equal(reverted.result.operation, "unchanged");
  assert.equal(reverted.result.hasPersistedChangeSet, false);
  const final = await request(versionPath);
  assert.deepEqual(current(final), baseline);
  assert.equal(
    (await request(`${versionPath}/change-set`)).hasPersistedChangeSet,
    false,
  );
  assert.notEqual(
    version(final).draftVersionToken,
    version(readback).draftVersionToken,
  );
  return {
    vertices: baseline.coordinates.length,
    commands,
    saveReadbackRevertReadback: true,
    replayConfirmed: true,
  };
}
