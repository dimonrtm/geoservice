SELECT
    ds.id,
    ds.work_order_id,
    ds.base_network_revision,
    ds.status,
    f.feature_id,
    f.feature_type,
    f.network_version,
    ST_AsEWKB(f.geometry) AS geometry_ewkb
FROM utility_network.default_states ds
LEFT JOIN utility_network.default_state_features f
    ON f.default_state_id = ds.id
    AND f.feature_id = :feature_id
WHERE ds.id = :default_state_id
