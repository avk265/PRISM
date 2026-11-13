-- generated TPC-H-schema training query (seed 7, #206, family spj_agg); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       AVG(o_totalprice) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
LIMIT 100
