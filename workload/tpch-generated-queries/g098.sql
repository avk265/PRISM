-- generated TPC-H-schema training query (seed 7, #98, family topn); not an official TPC-H query
SELECT o_orderkey AS ok, o_totalprice AS m0, o_orderdate AS od
FROM orders
WHERE o_orderstatus = 'P'
  AND o_orderpriority IN ('1-URGENT', '5-LOW', '2-HIGH')
ORDER BY m0 DESC, ok
LIMIT 100
