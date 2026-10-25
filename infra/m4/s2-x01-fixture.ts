import { compose } from "./recovery-helpers";
export async function createIndependentWorkOrders() {
  const sql = `DO $$ DECLARE source_state uuid; new_state uuid; new_work uuid; label text; BEGIN
 SELECT d.id INTO source_state FROM utility_network.default_states d JOIN work_order.work_orders w ON w.id=d.work_order_id WHERE w.code='WO-001';
 INSERT INTO "user".users(id,email,password_hash,role,is_active) SELECT gen_random_uuid(),'x01.other@example.local',password_hash,'editor',true FROM "user".users WHERE email='alexey.editor@example.local' ON CONFLICT(email) DO NOTHING;
 FOREACH label IN ARRAY ARRAY['X01-A','X01-B','X01-C'] LOOP
 new_work:=gen_random_uuid(); new_state:=gen_random_uuid();
 INSERT INTO work_order.work_orders(id,code,title,description,status,aoi_id,assignee_user_id,created_by_user_id) SELECT new_work,label,label,'Изолированный тестовый fixture','assigned',aoi_id,assignee_user_id,created_by_user_id FROM work_order.work_orders WHERE code='WO-001';
 INSERT INTO utility_network.default_states(id,work_order_id,network_state_id,base_network_revision,status) SELECT new_state,new_work,network_state_id,base_network_revision,status FROM utility_network.default_states WHERE id=source_state;
 INSERT INTO utility_network.default_state_features(default_state_id,feature_id,asset_code,feature_type,geometry,properties,network_version) SELECT new_state,md5(feature_id::text||new_state::text)::uuid,asset_code,feature_type,geometry,properties,network_version FROM utility_network.default_state_features WHERE default_state_id=source_state;
 INSERT INTO utility_network.default_state_associations(default_state_id,association_id,association_type,from_feature_id,to_feature_id,properties,network_version) SELECT new_state,md5(association_id::text||new_state::text)::uuid,association_type,md5(from_feature_id::text||new_state::text)::uuid,md5(to_feature_id::text||new_state::text)::uuid,properties,network_version FROM utility_network.default_state_associations WHERE default_state_id=source_state;
 END LOOP; END $$;`;
  await compose(
    "exec",
    "-T",
    "db",
    "psql",
    "-U",
    "postgres",
    "-d",
    "m4_test",
    "-v",
    "ON_ERROR_STOP=1",
    "-c",
    sql,
  );
}
