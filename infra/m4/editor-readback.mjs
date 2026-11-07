import assert from "node:assert/strict";

export function isEditVersionMap(url) {
  return /\/work-orders\/[^/]+\/edit-versions\/[^/]+$/.test(
    new URL(url).pathname,
  );
}

// Build a smoke observation from the same three public resources used by the editor.
export async function editorReadback(page, mapResponse) {
  const map = await mapResponse.json();
  assert.equal(mapResponse.status(), 200);
  const path = mapResponse.url();
  const headers = {
    Authorization: await mapResponse.request().headerValue("Authorization"),
  };
  async function get(suffix) {
    const response = await page.request.get(path + suffix, { headers });
    assert.equal(response.status(), 200);
    return response.json();
  }
  const changes = await get("/change-set");
  const version = map.workOrder.editVersion;
  assert.equal(changes.draftVersionToken, version.draftVersionToken);
  if (changes.changeSet) {
    const baseline = await get(
      `/features/${changes.changeSet.featureId}/baseline`,
    );
    assert.equal(baseline.featureId, changes.changeSet.featureId);
    changes.changeSet.baselineGeometry = baseline.baselineGeometry;
  }
  Object.assign(version, changes);
  return map;
}
