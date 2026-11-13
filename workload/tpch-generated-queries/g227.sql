-- generated TPC-H-schema training query (seed 7, #227, family topn); not an official TPC-H query
SELECT o_orderkey AS ok, o_totalprice AS m0, o_orderdate AS od
FROM orders
WHERE o_orderpriority IN ('3-MEDIUM', '1-URGENT', '2-HIGH')
  AND o_orderdate >= DATE '1995-04-01' AND o_orderdate < DATE '1995-01-01'
ORDER BY m0 DESC, ok
LIMIT 100
