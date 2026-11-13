-- generated TPC-H-schema training query (seed 7, #213, family topn); not an official TPC-H query
SELECT o_orderkey AS ok, o_totalprice AS m0, o_orderdate AS od
FROM orders
WHERE o_orderstatus = 'F'
  AND o_totalprice > 1000
ORDER BY m0 DESC, ok
LIMIT 100
