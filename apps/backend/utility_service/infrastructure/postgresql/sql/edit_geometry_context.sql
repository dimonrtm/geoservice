SELECT
    ev.draft_revision,
    wo.status AS work_order_status,
    wo.assignee_user_id,
    f.feature_id,
    f.feature_type,
    f.operation,
    f.network_version,
    ST_AsEWKB(f.geometry) AS current_ewkb,
    ds.id AS baseline_state_id,
    ds.work_order_id AS baseline_work_order_id,
    ds.base_network_revision AS baseline_revision,
    ds.status AS baseline_status,
    b.feature_id AS baseline_feature_id,
    b.feature_type AS baseline_feature_type,
    b.network_version AS baseline_network_version,
    ST_AsEWKB(b.geometry) AS baseline_ewkb,
    ST_AsEWKB(aoi.geometry) AS aoi_ewkb,
    ARRAY(
        SELECT other.feature_id
        FROM work_order.edit_version_features other
        WHERE other.edit_version_id = ev.id
            AND other.feature_id <> :feature_id
            AND other.operation <> 'unchanged'
        ORDER BY other.feature_id
    ) AS other_changed_feature_ids
FROM work_order.edit_versions ev
JOIN work_order.work_orders wo ON wo.id = ev.work_order_id
LEFT JOIN work_order.edit_version_features f
    ON f.edit_version_id = ev.id
    AND f.feature_id = :feature_id
LEFT JOIN utility_network.default_states ds ON ds.id = ev.default_state_id
LEFT JOIN utility_network.default_state_features b
    ON b.default_state_id = ds.id
    AND b.feature_id = :feature_id
LEFT JOIN work_order.aois aoi ON aoi.id = wo.aoi_id
WHERE ev.id = :edit_version_id
    AND ev.work_order_id = :work_order_id
