WITH geometries AS MATERIALIZED (
    SELECT
        ST_GeomFromEWKB(:geometry_ewkb) AS g,
        ST_GeomFromEWKB(:aoi_ewkb) AS a
), points AS (
    SELECT
        d.path,
        ST_X(d.geom) AS x,
        ST_Y(d.geom) AS y,
        lag(ST_X(d.geom)) OVER (ORDER BY d.path) AS previous_x,
        lag(ST_Y(d.geom)) OVER (ORDER BY d.path) AS previous_y
    FROM geometries, LATERAL ST_DumpPoints(g) d
), flags AS MATERIALIZED (
    SELECT
        g,
        a,
        GeometryType(g) = 'LINESTRING'
            AND ST_SRID(g) = 4326
            AND ST_NDims(g) = 2
            AND NOT EXISTS (
                SELECT 1
                FROM points
                WHERE NOT (x BETWEEN -180 AND 180 AND y BETWEEN -90 AND 90)
            ) AS shape_ok,
        NOT ST_IsEmpty(g) AS nonempty,
        ST_IsValid(g) AS valid,
        ST_IsSimple(g) AS simple,
        NOT EXISTS (
            SELECT 1
            FROM points
            WHERE x = previous_x AND y = previous_y
        ) AS no_zero_segments,
        GeometryType(a) IN ('POLYGON', 'MULTIPOLYGON')
            AND ST_SRID(a) = 4326
            AND ST_NDims(a) = 2
            AND NOT ST_IsEmpty(a)
            AND ST_IsValid(a)
            AND NOT EXISTS (
                SELECT 1
                FROM ST_DumpPoints(a) p
                WHERE NOT (
                    ST_X(p.geom) BETWEEN -180 AND 180
                    AND ST_Y(p.geom) BETWEEN -90 AND 90
                )
            ) AS aoi_valid
    FROM geometries
)
SELECT
    shape_ok,
    nonempty,
    valid,
    simple,
    no_zero_segments,
    aoi_valid,
    CASE
        WHEN shape_ok AND nonempty AND valid AND simple AND no_zero_segments AND aoi_valid
            THEN ST_Covers(a, g)
        ELSE false
    END AS aoi_covered
FROM flags
