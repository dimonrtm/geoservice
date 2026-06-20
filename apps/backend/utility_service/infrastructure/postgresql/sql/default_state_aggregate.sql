SELECT
    state.id,
    state.work_order_id,
    state.network_state_id,
    state.base_network_revision,
    state.status,
    state.created_at,
    state.updated_at,
    COALESCE(
        (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'default_state_id', feature.default_state_id,
                    'feature_id', feature.feature_id,
                    'asset_code', feature.asset_code,
                    'feature_type', feature.feature_type,
                    'geometry_ewkt', ST_AsEWKT(feature.geometry),
                    'properties', feature.properties,
                    'network_version', feature.network_version
                )
                ORDER BY feature.asset_code, feature.feature_id
            )
            FROM utility_network.default_state_features AS feature
            WHERE feature.default_state_id = state.id
        ),
        '[]'::jsonb
    ) AS features,
    COALESCE(
        (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'default_state_id', association.default_state_id,
                    'association_id', association.association_id,
                    'association_type', association.association_type,
                    'from_feature_id', association.from_feature_id,
                    'to_feature_id', association.to_feature_id,
                    'properties', association.properties,
                    'network_version', association.network_version
                )
                ORDER BY association.association_id
            )
            FROM utility_network.default_state_associations AS association
            WHERE association.default_state_id = state.id
        ),
        '[]'::jsonb
    ) AS associations
FROM utility_network.default_states AS state
WHERE state.work_order_id = :work_order_id
  AND state.status = :active_status
