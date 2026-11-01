import assert from "node:assert/strict";

export function buildLargeLine(sourceCoordinates) {
  assert.equal(sourceCoordinates.length, 3, "Expected three-vertex seed L-003");
  const [start, editable, end] = sourceCoordinates;
  const coordinates = [start, editable];
  // Вершина 1 и свободное место вокруг неё сохраняются. Уплотняется дальняя
  // половина последнего сегмента; endpoints и направление не меняются.
  for (let i = 0; i <= 60_000; i++) {
    const t = 0.5 + i / 120_000;
    coordinates.push(
      editable.map((v, axis) => Number((v + (end[axis] - v) * t).toFixed(9))),
    );
  }
  const line = { type: "LineString", coordinates };
  assert.ok(Buffer.byteLength(JSON.stringify(line)) > 1_100_000);
  for (let i = 1; i < coordinates.length; i++)
    assert.notDeepEqual(coordinates[i], coordinates[i - 1]);
  return line;
}

export async function prepareFixture(sql) {
  assert.equal(await sql("SELECT count(*) FROM work_order.edit_versions"), "0");
  const source = JSON.parse(
    await sql(`
    SELECT json_build_object('featureId', f.feature_id, 'workOrderId', d.work_order_id,
      'geometry', ST_AsGeoJSON(f.geometry)::json)
    FROM utility_network.default_state_features f
    JOIN utility_network.default_states d ON d.id=f.default_state_id
    JOIN work_order.work_orders w ON w.id=d.work_order_id
    WHERE w.code='WO-001' AND f.asset_code='L-003'`),
  );
  const geometry = buildLargeLine(source.geometry.coordinates);
  const literal = JSON.stringify(geometry);
  await sql(`BEGIN;
    UPDATE utility_network.network_features SET geometry=ST_SetSRID(ST_GeomFromGeoJSON('${literal}'),4326)
      WHERE id='${source.featureId}';
    UPDATE utility_network.default_state_features SET geometry=ST_SetSRID(ST_GeomFromGeoJSON('${literal}'),4326)
      WHERE feature_id='${source.featureId}';
    COMMIT;`);
  const checks = JSON.parse(
    await sql(`
    SELECT json_build_object('valid', ST_IsValid(f.geometry), 'simple', ST_IsSimple(f.geometry),
      'covered', ST_CoveredBy(f.geometry,a.geometry), 'vertices', ST_NPoints(f.geometry),
      'nonzeroSegments', NOT EXISTS (SELECT 1 FROM (
        SELECT geom, lag(geom) OVER (ORDER BY path) AS previous
        FROM ST_DumpPoints(f.geometry)
      ) points WHERE ST_Equals(geom,previous)))
    FROM utility_network.default_state_features f
    JOIN utility_network.default_states d ON d.id=f.default_state_id
    JOIN work_order.work_orders w ON w.id=d.work_order_id
    JOIN work_order.aois a ON a.id=w.aoi_id
    WHERE w.id='${source.workOrderId}' AND f.feature_id='${source.featureId}'`),
  );
  for (const key of ["valid", "simple", "covered", "nonzeroSegments"])
    assert.equal(checks[key], true, key);
  return {
    workOrderId: source.workOrderId,
    featureId: source.featureId,
    coordinates: geometry.coordinates,
    checks,
  };
}
