-- generated TPC-H-schema training query (seed 7, #279, family topn); not an official TPC-H query
SELECT l_orderkey AS ok, l_linenumber AS ln, l_extendedprice AS m0
FROM lineitem
WHERE l_shipdate >= DATE '1995-01-01' AND l_shipdate < DATE '1995-01-01'
ORDER BY m0 DESC, ok, ln
LIMIT 100
