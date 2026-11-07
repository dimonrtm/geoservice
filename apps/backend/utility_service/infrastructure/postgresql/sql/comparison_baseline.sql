SELECT state.id, state.work_order_id, state.base_network_revision, state.status,
       COALESCE((
           SELECT jsonb_agg(jsonb_build_object(
               'feature_id', feature.feature_id,
               'feature_type', feature.feature_type,
               'geometry_ewkb', encode(ST_AsEWKB(feature.geometry), 'hex')
           ) ORDER BY feature.feature_id)
           FROM utility_network.default_state_features AS feature
           WHERE feature.default_state_id = state.id
       ), '[]'::jsonb) AS features
FROM utility_network.default_states AS state
WHERE state.id = :default_state_id
