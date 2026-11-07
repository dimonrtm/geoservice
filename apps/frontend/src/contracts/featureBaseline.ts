import {
  record,
  isLineStringXY,
  ProtocolError,
  type LineStringXY,
} from "./workspace-edit";
export type FeatureBaseline = {
  featureId: string;
  baselineGeometry: LineStringXY;
};
export function parseFeatureBaseline(
  value: unknown,
  featureId: string,
): FeatureBaseline {
  if (
    !record(value) ||
    value.featureId !== featureId ||
    !isLineStringXY(value.baselineGeometry)
  )
    throw new ProtocolError();
  return { featureId, baselineGeometry: value.baselineGeometry };
}
