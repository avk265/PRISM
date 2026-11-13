-- generated TPC-H-schema training query (seed 7, #308, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       l_returnflag AS returnflag,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       COUNT(*) AS m1,
       COUNT(*) AS m2
FROM customer, orders, lineitem, supplier, part
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey = p_partkey
  AND p_type LIKE '%BRASS'
  AND c_mktsegment = 'HOUSEHOLD'
  AND l_shipmode IN ('MAIL', 'AIR', 'SHIP')
GROUP BY year(l_shipdate), l_returnflag
ORDER BY m0 DESC, ship_year, returnflag
LIMIT 100
