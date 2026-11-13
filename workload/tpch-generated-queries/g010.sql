-- generated TPC-H-schema training query (seed 7, #10, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1,
       COUNT(DISTINCT o_custkey) AS m2
FROM orders, lineitem, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND o_orderpriority IN ('1-URGENT', '2-HIGH')
GROUP BY l_returnflag
HAVING COUNT(*) > 5
ORDER BY m0 DESC, returnflag
LIMIT 100
