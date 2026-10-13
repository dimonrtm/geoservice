WITH workspace_context AS (
    SELECT
        work_order.id AS work_order_id,
        work_order.code AS work_order_code,
        work_order.title AS work_order_title,
        work_order.description AS work_order_description,
        work_order.status AS work_order_status,
        work_order.assignee_user_id AS work_order_assignee_user_id,
        edit_version.id AS edit_version_id,
        edit_version.status AS edit_version_status,
        edit_version.base_network_revision AS edit_version_base_network_revision,
        edit_version.draft_revision AS edit_version_draft_revision,
        edit_version.default_state_id AS edit_version_default_state_id,
        baseline.id AS baseline_state_id,
        baseline.work_order_id AS baseline_work_order_id,
        baseline.base_network_revision AS baseline_base_network_revision,
        baseline.status AS baseline_status,
        aoi.id AS aoi_id,
        aoi.name AS aoi_name,
        aoi.description AS aoi_description,
        aoi.geometry AS aoi_geometry
    FROM work_order.work_orders AS work_order
    JOIN work_order.edit_versions AS edit_version
      ON edit_version.work_order_id = work_order.id
    LEFT JOIN utility_network.default_states AS baseline
      ON baseline.id = edit_version.default_state_id
    LEFT JOIN work_order.aois AS aoi
      ON aoi.id = work_order.aoi_id
    WHERE work_order.id = :work_order_id
      AND edit_version.id = :edit_version_id
),
workspace_features AS MATERIALIZED (
    SELECT
        feature.edit_version_id,
        feature.feature_id,
        feature.asset_code,
        feature.feature_type,
        feature.geometry,
        feature.properties,
        feature.network_version,
        feature.operation
    FROM workspace_context AS context
    JOIN work_order.edit_version_features AS feature
      ON feature.edit_version_id = context.edit_version_id
    WHERE ST_Intersects(context.aoi_geometry, feature.geometry)
),
current_features AS (
    SELECT feature.*
    FROM workspace_context AS context
    JOIN work_order.edit_version_features AS feature
      ON feature.edit_version_id = context.edit_version_id
),
baseline_features AS (
    SELECT feature.*
    FROM workspace_context AS context
    JOIN utility_network.default_state_features AS feature
      ON feature.default_state_id = context.edit_version_default_state_id
),
draft_pairs_json AS (
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'feature_id', COALESCE(current.feature_id, baseline.feature_id),
                'current_feature_type', current.feature_type,
                'baseline_feature_type', baseline.feature_type,
                'current_geometry_ewkb', encode(ST_AsEWKB(current.geometry), 'hex'),
                'baseline_geometry_ewkb', encode(ST_AsEWKB(baseline.geometry), 'hex'),
                'operation', current.operation,
                'visible', EXISTS (
                    SELECT 1 FROM workspace_features AS visible
                    WHERE visible.feature_id = current.feature_id
                )
            )
            ORDER BY COALESCE(current.feature_id, baseline.feature_id)
        ),
        '[]'::jsonb
    ) AS draft_feature_pairs
    FROM current_features AS current
    FULL OUTER JOIN baseline_features AS baseline
      ON baseline.feature_id = current.feature_id
),
features_json AS (
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'id', feature.feature_id,
                'asset_code', feature.asset_code,
                'feature_type', feature.feature_type,
                'geometry_ewkb', encode(ST_AsEWKB(feature.geometry), 'hex'),
                'properties', feature.properties,
                'network_version', feature.network_version,
                'operation', feature.operation
            )
            ORDER BY feature.asset_code, feature.feature_id
        ),
        '[]'::jsonb
    ) AS features_data
    FROM workspace_features AS feature
),
associations_json AS (
    SELECT COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'id', association.association_id,
                'from_feature_id', association.from_feature_id,
                'to_feature_id', association.to_feature_id,
                'association_type', association.association_type,
                'version', association.network_version
            )
            ORDER BY
                association.from_feature_id,
                association.to_feature_id,
                association.association_type,
                association.association_id
        ),
        '[]'::jsonb
    ) AS associations_data
    FROM workspace_context AS context
    JOIN work_order.edit_version_associations AS association
      ON association.edit_version_id = context.edit_version_id
    JOIN workspace_features AS from_feature
      ON from_feature.feature_id = association.from_feature_id
    JOIN workspace_features AS to_feature
      ON to_feature.feature_id = association.to_feature_id
)
SELECT
    context.work_order_id,
    context.work_order_code,
    context.work_order_title,
    context.work_order_description,
    context.work_order_status,
    context.work_order_assignee_user_id,
    context.edit_version_id,
    context.edit_version_status,
    context.edit_version_base_network_revision,
    context.edit_version_draft_revision,
    context.edit_version_default_state_id,
    context.baseline_state_id,
    context.baseline_work_order_id,
    context.baseline_base_network_revision,
    context.baseline_status,
    context.aoi_id,
    context.aoi_name,
    context.aoi_description,
    ST_AsGeoJSON(context.aoi_geometry)::jsonb AS aoi_geometry_data,
    jsonb_build_array(
        ST_XMin(Box2D(context.aoi_geometry)),
        ST_YMin(Box2D(context.aoi_geometry)),
        ST_XMax(Box2D(context.aoi_geometry)),
        ST_YMax(Box2D(context.aoi_geometry))
    ) AS aoi_extent,
    features_json.features_data,
    associations_json.associations_data,
    draft_pairs_json.draft_feature_pairs
FROM workspace_context AS context
CROSS JOIN features_json
CROSS JOIN associations_json
CROSS JOIN draft_pairs_json
