-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       year(l_shipdate) AS ship_year,
       l_linestatus AS linestatus,
       SUM(l_quantity) AS m0,
       SUM(l_extendedprice * (1 - l_discount)) AS m1
FROM lineitem, supplier
WHERE l_suppkey = s_suppkey
  AND s_acctbal > -500
  AND l_shipmode IN ('AIR', 'REG AIR')
GROUP BY l_returnflag, year(l_shipdate), l_linestatus
ORDER BY m0 DESC, returnflag, ship_year, linestatus
LIMIT 100
