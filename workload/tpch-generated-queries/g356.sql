-- generated TPC-H-schema training query (seed 7, #356, family spj_agg); not an official TPC-H query
SELECT p_brand AS brand,
       l_shipmode AS shipmode,
       COUNT(*) AS m0,
       COUNT(*) AS m1
FROM lineitem, orders, part
WHERE l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND o_orderdate >= DATE '1994-09-01' AND o_orderdate < DATE '1997-01-01'
  AND p_type LIKE '%BRASS'
  AND l_receiptdate > l_commitdate
GROUP BY p_brand, l_shipmode
HAVING COUNT(*) > 20
ORDER BY m0 DESC, brand, shipmode
LIMIT 100
