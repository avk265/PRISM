-- generated TPC-H-schema training query (seed 7, #329, family topn); not an official TPC-H query
SELECT o_orderkey AS ok, o_totalprice AS m0, o_orderdate AS od
FROM orders
WHERE o_orderpriority IN ('3-MEDIUM')
ORDER BY m0 DESC, ok
LIMIT 100
