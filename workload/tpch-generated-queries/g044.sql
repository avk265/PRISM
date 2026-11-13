-- generated TPC-H-schema training query (seed 7, #44, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       SUM(o_totalprice) AS m0,
       COUNT(*) AS m1
FROM lineitem, orders, supplier
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_quantity < 40
  AND o_orderpriority IN ('3-MEDIUM', '1-URGENT')
  AND s_acctbal > 5000
GROUP BY year(l_shipdate)
ORDER BY m0 DESC, ship_year
LIMIT 100
