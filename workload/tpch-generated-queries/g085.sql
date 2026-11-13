-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       COUNT(DISTINCT o_custkey) AS m0,
       AVG(l_discount) AS m1,
       SUM(o_totalprice) AS m2
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND o_orderstatus = 'O'
  AND c_acctbal > 8000
  AND l_receiptdate > l_commitdate
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
LIMIT 100
