---
title: Фактическая проверка demo-набора и fixture L-003
type: verification-report
status: active
created: 2026-11-08
updated: 2026-11-08
source: Docker geo-postgis и utility_service; read-only SELECT; чистая функция prepare_geometry
tags: [demo, fixture, metadata, runtime-verification]
---

# Фактическая проверка demo-набора

## Результат и область

08.11.2026, 18:14–18:15 +05:00: локальная БД `geo` в `geo-postgis` содержит пригодную fixture L-003 для технического упражнения перемещения одной внутренней вершины. Проверены реальные строки БД, не только seed. Backend `utility_service`, PostGIS и frontend работали со статусом healthy. Alembic revision БД: `e9f1a2b3c4d5`.

Два блока SELECT выполнены каждый в `REPEATABLE READ READ ONLY`; `transaction_read_only=on`. Revision версии в обоих блоках — 49. Второй блок независимо проверил полное равенство current/baseline, геометрию, AOI и связи. Проверка чистой функции в backend не обращалась к БД и не выполняла Save. Данные, контейнеры и volumes не изменялись.

Это наблюдение локального экземпляра в указанное время. Оно не является новой end-to-end проверкой HTTP Save, авторизации или UI и не доказывает позиционную точность на местности.

## Идентичность и persisted metadata

| Поле | Фактическое значение |
| --- | --- |
| Feeder | synthetic_utility_feeder_01 |
| Feeder ID | 6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101 |
| WorkOrder | WO-001, 6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401, in_progress |
| EditVersion | 6525a69d-3b41-4564-9b63-562e504adc21, open |
| DefaultState | 9357abe7-28fe-4473-b12c-194ae8238ce8 |
| Base network revision / draft revision | 1 / 49 |
| Feature L-003 | 6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0213 |
| CRS / размерность | SRID 4326 / XY (2D) |
| Coordinate unit | Градусы в контракте EPSG:4326; X=долгота, Y=широта |
| geometry_xy_resolution | 0.0000001 |
| geometry_rounding_mode | ROUND_HALF_AWAY_FROM_ZERO |
| geometry_policy_version | 1 |
| Origin / допустимые XY | 0/0; X [-180,180], Y [-90,90] — контракт кода запущенного backend, не отдельные metadata-столбцы |
| xyTolerance | Отдельного persisted поля в текущем контракте нет; не приравнивается к resolution или позиционному допуску |
| Transformations | В проверенном пути canonicalization CRS-преобразование не выполняется; это не доказательство истории любых прежних импортов |

Runtime-код `GeometryPolicy`, `quantize_ordinate` и `prepare_geometry` прочитан из контейнера `utility_service`. Результаты согласуются с [описанием fixture](../../Code_wiki/архитектура/edit_geometry_fixture_metadata.md). Синтетические координаты совпадают с seed; независимое происхождение реальных измерений для этой fixture не заявляется.

## Геометрия и связи

Фактические network/baseline/current L-003:
```text
(65.520,44.820) → (65.525,44.8205) → (65.530,44.820)
```

- 3 вершины; SRID 4326, XY; valid=true, simple=true.
- Полная current geometry покрывается AOI.
- Начало совпадает с J-003, конец — с J-004.
- Средняя вершина не пересекается с junction/device текущей версии.
- В network присутствуют connectivity D-002 → L-003 и D-003 → L-003.
- Все 9 associations current равны baseline по ID, типу, концам, properties и network_version.
- Все 19 features current равны baseline по ID, asset_code, feature_type, EWKB, properties и network_version; симметрическая разность пуста.
- Все operation имеют unchanged; все координаты current лежат на сохранённой сетке.
- Другие пять network lines имеют по две вершины и не подходят для этого конкретного UI-упражнения.

AOI:
```text
POLYGON((65.495 44.795,65.545 44.795,65.545 44.835,65.495 44.835,65.495 44.795))
```

## Кандидат без сохранения

Проверен кандидат:
```text
(65.520,44.820) → (65.525,44.8215) → (65.530,44.820)
```

В PostGIS: valid/simple=true, покрытие AOI=true, число вершин и концы сохранены, изменение ненулевое. Чистая функция `prepare_geometry` с прочитанной policy вернула `vertex_index=1`, `rejection_code=None`; средняя Y канонизирована в `44.8215000`. Кандидат не записывался. Это синтетическое упражнение, не измеренная поправка.

## История и текущее состояние

Найдены 48 успешных command rows (HTTP status в сохранённом результате 200), 28 событий change_set_persisted и 20 change_set_cleared. Последнее событие — change_set_cleared, revision 48 → 49, 08.11.2026 11:56:50.772742 UTC. Сейчас diff пуст: история действий не означает наличие текущих изменений.

## Последствия для открытых вопросов

Два вопроса в [[Wiki/_registry/questions]] о фактических demo metadata и выборе fixture отвечены **для этого экземпляра и revision 49**. Неподдерживаемые metadata названы явно; их отсутствие не выдаётся за неизвестный численный параметр.

POSITIONAL_ACCURACY_UNVERIFIED сохраняет прежний смысл: позиционное evidence не получено. FU-2026-10-11-001 остаётся open для сверки остальной доменной очереди с реализацией; техническая часть metadata/fixture больше не является его открытым остатком. Это результат проверки, не новое устойчивое техническое решение: repository-change ingest и agent-memory entry не требуются.

## Воспроизводимые запросы

Запуск: передать SQL на stdin `psql -X -v ON_ERROR_STOP=1` внутри geo-postgis, используя локальные POSTGRES_USER/POSTGRES_DB без вывода их значений. SQL содержит только SELECT и границы read-only транзакции.

### Набор, metadata и история

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT now() AS observed_at,current_database(),current_setting('transaction_read_only') AS read_only;
SELECT version_num FROM public.alembic_version;
SELECT id,code,is_active FROM utility_network.feeders;
SELECT w.id,w.code,w.status,ST_AsText(a.geometry) AS aoi,ST_SRID(a.geometry) AS aoi_srid FROM work_order.work_orders w LEFT JOIN work_order.aois a ON a.id=w.aoi_id;
SELECT id,work_order_id,default_state_id,status,base_network_revision,draft_revision,geometry_xy_resolution,geometry_rounding_mode,geometry_policy_version FROM work_order.edit_versions;
SELECT f.asset_code,f.id,ST_AsText(f.geometry) AS geometry,ST_SRID(f.geometry) AS srid,ST_NDims(f.geometry) AS dimensions,ST_NPoints(f.geometry) AS vertices,ST_IsValid(f.geometry) AS valid,ST_IsSimple(f.geometry) AS simple,ST_CoveredBy(f.geometry,a.geometry) AS in_aoi FROM utility_network.network_features f CROSS JOIN work_order.work_orders w JOIN work_order.aois a ON a.id=w.aoi_id WHERE w.code='WO-001' AND f.asset_code LIKE 'L-%' ORDER BY f.asset_code;
SELECT f.edit_version_id,f.feature_id,f.asset_code,f.operation,ST_AsText(f.geometry) AS current_geometry,ST_AsText(b.geometry) AS baseline_geometry,ST_OrderingEquals(f.geometry,b.geometry) AS same_geometry,f.properties=b.properties AS same_attributes,f.network_version=b.network_version AS same_network_version FROM work_order.edit_version_features f JOIN work_order.edit_versions v ON v.id=f.edit_version_id LEFT JOIN utility_network.default_state_features b ON b.default_state_id=v.default_state_id AND b.feature_id=f.feature_id WHERE f.asset_code='L-003';
SELECT n.association_type,f.asset_code AS from_asset,t.asset_code AS to_asset FROM utility_network.network_associations n JOIN utility_network.network_features f ON f.id=n.from_feature_id JOIN utility_network.network_features t ON t.id=n.to_feature_id WHERE f.asset_code='L-003' OR t.asset_code='L-003';
SELECT edit_version_id,event_type,count(*) FROM work_order.edit_version_change_events GROUP BY 1,2;
SELECT edit_version_id,state,response_status,rejection_code,count(*) FROM work_order.edit_version_commands GROUP BY 1,2,3,4;
COMMIT;
```

### Полная сверка и геометрия кандидата

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SELECT now() AS observed_at,id,draft_revision FROM work_order.edit_versions;
WITH f AS (SELECT v.id, (SELECT count(*) FROM work_order.edit_version_features e WHERE e.edit_version_id=v.id) AS current_count,(SELECT count(*) FROM utility_network.default_state_features b WHERE b.default_state_id=v.default_state_id) AS baseline_count,(SELECT count(*) FROM ( (SELECT feature_id,asset_code,feature_type,ST_AsEWKB(geometry),properties,network_version FROM work_order.edit_version_features WHERE edit_version_id=v.id EXCEPT SELECT feature_id,asset_code,feature_type,ST_AsEWKB(geometry),properties,network_version FROM utility_network.default_state_features WHERE default_state_id=v.default_state_id) UNION ALL (SELECT feature_id,asset_code,feature_type,ST_AsEWKB(geometry),properties,network_version FROM utility_network.default_state_features WHERE default_state_id=v.default_state_id EXCEPT SELECT feature_id,asset_code,feature_type,ST_AsEWKB(geometry),properties,network_version FROM work_order.edit_version_features WHERE edit_version_id=v.id)) d) AS differing_rows FROM work_order.edit_versions v) SELECT * FROM f;
SELECT v.id,(SELECT count(*) FROM work_order.edit_version_associations WHERE edit_version_id=v.id) AS current_associations,(SELECT count(*) FROM utility_network.default_state_associations WHERE default_state_id=v.default_state_id) AS baseline_associations,(SELECT count(*) FROM ((SELECT association_id,association_type,from_feature_id,to_feature_id,properties,network_version FROM work_order.edit_version_associations WHERE edit_version_id=v.id EXCEPT SELECT association_id,association_type,from_feature_id,to_feature_id,properties,network_version FROM utility_network.default_state_associations WHERE default_state_id=v.default_state_id) UNION ALL (SELECT association_id,association_type,from_feature_id,to_feature_id,properties,network_version FROM utility_network.default_state_associations WHERE default_state_id=v.default_state_id EXCEPT SELECT association_id,association_type,from_feature_id,to_feature_id,properties,network_version FROM work_order.edit_version_associations WHERE edit_version_id=v.id)) d) AS differing_rows FROM work_order.edit_versions v;
SELECT operation,count(*) FROM work_order.edit_version_features GROUP BY 1;
SELECT operation,count(*) FROM work_order.edit_version_associations GROUP BY 1;
SELECT f.asset_code,ST_AsText(f.geometry),ST_SRID(f.geometry),ST_NDims(f.geometry),ST_IsValid(f.geometry),ST_IsSimple(f.geometry),ST_CoveredBy(f.geometry,a.geometry) AS current_in_aoi,ST_Equals(ST_StartPoint(f.geometry),j3.geometry) AS start_is_j003,ST_Equals(ST_EndPoint(f.geometry),j4.geometry) AS end_is_j004,NOT EXISTS (SELECT 1 FROM work_order.edit_version_features p WHERE p.edit_version_id=f.edit_version_id AND p.feature_type IN ('junction','device') AND ST_Intersects(ST_PointN(f.geometry,2),p.geometry)) AS middle_not_on_device_or_junction FROM work_order.edit_version_features f JOIN work_order.edit_versions v ON v.id=f.edit_version_id JOIN work_order.work_orders w ON w.id=v.work_order_id JOIN work_order.aois a ON a.id=w.aoi_id JOIN work_order.edit_version_features j3 ON j3.edit_version_id=v.id AND j3.asset_code='J-003' JOIN work_order.edit_version_features j4 ON j4.edit_version_id=v.id AND j4.asset_code='J-004' WHERE f.asset_code='L-003';
WITH g AS (SELECT ST_GeomFromText('LINESTRING(65.520 44.820,65.525 44.8215,65.530 44.820)',4326) AS candidate)
SELECT ST_IsValid(candidate),ST_IsSimple(candidate),ST_CoveredBy(candidate,a.geometry) AS candidate_in_aoi,ST_NPoints(candidate)=ST_NPoints(f.geometry) AS same_count,ST_Equals(ST_StartPoint(candidate),ST_StartPoint(f.geometry)) AND ST_Equals(ST_EndPoint(candidate),ST_EndPoint(f.geometry)) AS same_endpoints,NOT ST_OrderingEquals(candidate,f.geometry) AS nonzero_change FROM g CROSS JOIN work_order.edit_version_features f JOIN work_order.edit_versions v ON v.id=f.edit_version_id JOIN work_order.work_orders w ON w.id=v.work_order_id JOIN work_order.aois a ON a.id=w.aoi_id WHERE f.asset_code='L-003';
SELECT bool_and(mod(ST_X(p.geom)::numeric,v.geometry_xy_resolution)=0 AND mod(ST_Y(p.geom)::numeric,v.geometry_xy_resolution)=0) AS all_current_points_on_grid FROM work_order.edit_version_features f JOIN work_order.edit_versions v ON v.id=f.edit_version_id CROSS JOIN LATERAL ST_DumpPoints(f.geometry) p;
SELECT event_type,draft_revision_before,draft_revision_after,occurred_at FROM work_order.edit_version_change_events ORDER BY occurred_at DESC LIMIT 3;
COMMIT;
```
