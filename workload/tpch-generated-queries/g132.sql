-- generated TPC-H-schema training query (seed 7, #132, family topn); not an official TPC-H query
SELECT l_orderkey AS ok, l_linenumber AS ln, l_extendedprice AS m0
FROM lineitem
WHERE l_shipmode IN ('FOB')
  AND l_quantity < 25
ORDER BY m0 DESC, ok, ln
LIMIT 100
