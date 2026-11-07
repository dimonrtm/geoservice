SELECT
    wo.id AS work_order_id,
    wo.assignee_user_id,
    wo.status AS work_order_status,
    version.id AS edit_version_id,
    version.status AS edit_version_status,
    version.base_network_revision AS edit_version_base_network_revision,
    version.draft_revision AS edit_version_draft_revision,
    version.default_state_id AS edit_version_default_state_id,
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'feature_id', feature.feature_id,
            'feature_type', feature.feature_type,
            'geometry_ewkb', encode(ST_AsEWKB(feature.geometry), 'hex'),
            'operation', feature.operation,
            'visible', ST_Intersects(aoi.geometry, feature.geometry)
        ) ORDER BY feature.feature_id)
        FROM work_order.edit_version_features AS feature
        WHERE feature.edit_version_id = version.id
          AND (CAST(:feature_id AS uuid) IS NULL OR feature.feature_id = :feature_id)
    ), '[]'::jsonb) AS features
FROM work_order.work_orders AS wo
JOIN work_order.edit_versions AS version ON version.work_order_id = wo.id
LEFT JOIN work_order.aois AS aoi ON aoi.id = wo.aoi_id
WHERE wo.id = :work_order_id AND version.id = :edit_version_id
