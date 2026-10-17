import type { Polygon, MultiPolygon, Position } from "geojson";
import type { WorkspaceResponse } from "@/contracts/work-orders";
import { isLineStringXY, type LineStringXY } from "@/contracts/workspace-edit";

export function lineSelectionBlockReason(
  workspace: WorkspaceResponse,
  featureId: string,
): string | null {
  const version = workspace.workOrder.editVersion;
  const feature = version.features.features.find(
    (item) => item.id === featureId,
  );
  if (!feature) return "Объект больше не доступен в рабочей области.";
  if (version.status !== "open")
    return "Рабочая версия закрыта для редактирования.";
  if (
    feature.properties.featureType !== "line" ||
    !isLineStringXY(feature.geometry)
  )
    return "Можно изменять только существующую линию с координатами XY.";
  if (!["unchanged", "updated"].includes(String(feature.properties.operation)))
    return "Созданный или удалённый объект недоступен для этой правки.";
  if (feature.geometry.coordinates.length !== 3)
    return "Для редактирования нужна линия с единственной внутренней вершиной.";
  if (
    version.changeSet &&
    (version.changeSet.featureId !== featureId ||
      version.changeSet.vertexIndex !== 1)
  )
    return "В этой версии уже сохранено изменение другой линии или вершины.";
  return null;
}

const cross = (a: Position, b: Position) => a[0]! * b[1]! - a[1]! * b[0]!;
const subtract = (a: Position, b: Position): Position => [
  a[0]! - b[0]!,
  a[1]! - b[1]!,
];
const same = (a: Position, b: Position) => a[0] === b[0] && a[1] === b[1];
function onSegment(p: Position, a: Position, b: Position): boolean {
  return (
    cross(subtract(p, a), subtract(b, a)) === 0 &&
    p[0]! >= Math.min(a[0]!, b[0]!) &&
    p[0]! <= Math.max(a[0]!, b[0]!) &&
    p[1]! >= Math.min(a[1]!, b[1]!) &&
    p[1]! <= Math.max(a[1]!, b[1]!)
  );
}

// Boundary is distinct from interior: hole boundaries are covered, hole interiors are not.
function ringLocation(
  p: Position,
  ring: Position[],
): "inside" | "outside" | "boundary" {
  let inside = false;
  for (let i = 1; i < ring.length; i++) {
    const a = ring[i - 1]!,
      b = ring[i]!;
    if (onSegment(p, a, b)) return "boundary";
    if (
      a[1]! > p[1]! !== b[1]! > p[1]! &&
      p[0]! < ((b[0]! - a[0]!) * (p[1]! - a[1]!)) / (b[1]! - a[1]!) + a[0]!
    )
      inside = !inside;
  }
  return inside ? "inside" : "outside";
}
function coveredPoint(p: Position, polygons: Position[][][]): boolean {
  return polygons.some((rings) => {
    const outer = ringLocation(p, rings[0]!);
    if (outer === "outside") return false;
    return rings.slice(1).every((ring) => ringLocation(p, ring) !== "inside");
  });
}
function coveredSegment(
  a: Position,
  b: Position,
  polygons: Position[][][],
): boolean {
  if (!coveredPoint(a, polygons) || !coveredPoint(b, polygons)) return false;
  const r = subtract(b, a);
  const axis = Math.abs(r[0]!) >= Math.abs(r[1]!) ? 0 : 1;
  const cuts = [0, 1];
  for (const rings of polygons)
    for (const ring of rings)
      for (let i = 1; i < ring.length; i++) {
        const c = ring[i - 1]!,
          d = ring[i]!,
          s = subtract(d, c),
          q = subtract(c, a);
        const denominator = cross(r, s);
        if (denominator === 0) {
          if (cross(q, r) === 0)
            for (const p of [c, d]) {
              const t = (p[axis]! - a[axis]!) / r[axis]!;
              if (t > 0 && t < 1) cuts.push(t);
            }
        } else {
          const t = cross(q, s) / denominator,
            u = cross(q, r) / denominator;
          if (t > 0 && t < 1 && u >= 0 && u <= 1) cuts.push(t);
        }
      }
  cuts.sort((x, y) => x - y);
  // Membership is constant between consecutive boundary intersections. Do not
  // merge nearby cuts: even a very narrow hole or gap must remain observable.
  for (let i = 1; i < cuts.length; i++) {
    if (cuts[i] === cuts[i - 1]) continue;
    const t = (cuts[i]! + cuts[i - 1]!) / 2;
    if (!coveredPoint([a[0]! + r[0]! * t, a[1]! + r[1]! * t], polygons))
      return false;
  }
  return true;
}

export function vertexMoveBlockReason(
  geometry: LineStringXY,
  aoi: Polygon | MultiPolygon,
): string | null {
  if (!isLineStringXY(geometry) || geometry.coordinates.length !== 3)
    return "Некорректные координаты линии.";
  const a = geometry.coordinates[0]!,
    middle = geometry.coordinates[1]!,
    b = geometry.coordinates[2]!;
  if (same(a, middle) || same(middle, b))
    return "Внутренняя вершина не может совпадать с концом линии.";
  if (
    same(a, b) ||
    (cross(subtract(middle, a), subtract(b, a)) === 0 &&
      !onSegment(middle, a, b))
  )
    return "Сегменты линии не должны накладываться друг на друга.";
  const polygons = aoi.type === "Polygon" ? [aoi.coordinates] : aoi.coordinates;
  if (
    !polygons.length ||
    polygons.some(
      (rings) =>
        !rings.length ||
        rings.some(
          (ring) =>
            ring.length < 4 ||
            !same(ring[0]!, ring[ring.length - 1]!) ||
            ring.some((p) => p.length !== 2 || !p.every(Number.isFinite)),
        ),
    )
  )
    return "Граница области работ недоступна для проверки.";
  if (
    !coveredSegment(a, middle, polygons) ||
    !coveredSegment(middle, b, polygons)
  )
    return "Линия выходит за область работ или пересекает её исключённый участок.";
  return null;
}
