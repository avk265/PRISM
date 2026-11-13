-- generated TPC-H-schema training query (seed 7, #283, family topn); not an official TPC-H query
SELECT l_orderkey AS ok, l_linenumber AS ln, l_extendedprice AS m0
FROM lineitem
WHERE l_discount BETWEEN 0.02 AND 0.1
  AND l_shipdate >= DATE '1992-01-01' AND l_shipdate < DATE '1999-01-01'
ORDER BY m0 DESC, ok, ln
LIMIT 100
