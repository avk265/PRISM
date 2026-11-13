-- generated TPC-H-schema training query (seed 7, #219, family spj_agg); not an official TPC-H query
SELECT s_suppkey AS s_suppkey,
       AVG(o_totalprice) AS m0,
       SUM(o_totalprice) AS m1
FROM lineitem, supplier, part, orders
WHERE l_suppkey = s_suppkey
  AND l_partkey = p_partkey
  AND l_orderkey = o_orderkey
  AND l_discount BETWEEN 0.0 AND 0.1
  AND o_orderstatus = 'O'
GROUP BY s_suppkey
HAVING COUNT(*) > 5
ORDER BY m0 DESC, s_suppkey
LIMIT 100
