-- generated TPC-H-schema training query (seed 7, #6, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       o_custkey AS custkey,
       COUNT(*) AS m0,
       COUNT(DISTINCT o_custkey) AS m1
FROM customer, orders, lineitem, part
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND o_orderstatus = 'O'
  AND l_quantity < 15
  AND c_mktsegment = 'HOUSEHOLD'
GROUP BY l_returnflag, o_custkey
HAVING COUNT(*) > 20
ORDER BY m0 DESC, returnflag, custkey
LIMIT 100
