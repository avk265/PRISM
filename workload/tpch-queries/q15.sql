-- TPC-H Query 15 (Top Supplier Query) converted to standard Spark SQL CTE format
WITH revenue0 AS (
    SELECT
        l_suppkey AS supplier_no,
        SUM(l_extendedprice * (1 - l_discount)) AS total_revenue
    FROM
        lineitem
    WHERE
        l_shipdate >= DATE '1994-06-01'
        AND l_shipdate < DATE '1994-06-01' + INTERVAL '3' MONTH
    GROUP BY
        l_suppkey
)
SELECT
    s.s_suppkey,
    s.s_name,
    s.s_address,
    s.s_phone,
    r.total_revenue
FROM
    supplier s
JOIN
    revenue0 r ON s.s_suppkey = r.supplier_no
WHERE
    r.total_revenue = (
        SELECT MAX(total_revenue) FROM revenue0
    )
ORDER BY
    s.s_suppkey;
