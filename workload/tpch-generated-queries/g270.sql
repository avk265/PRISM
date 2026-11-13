-- generated TPC-H-schema training query (seed 7, #270, family topn); not an official TPC-H query
SELECT l_orderkey AS ok, l_linenumber AS ln, l_extendedprice AS m0
FROM lineitem
WHERE l_returnflag = 'R'
  AND l_receiptdate > l_commitdate
ORDER BY m0 DESC, ok, ln
LIMIT 100
