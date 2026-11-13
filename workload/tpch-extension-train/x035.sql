-- generated TPC-H-schema training query (seed 11, #35, family outer_join); not an official TPC-H query
SELECT p_size AS psize, COUNT(l_orderkey) AS m0, SUM(l_quantity) AS m1
FROM part LEFT OUTER JOIN lineitem ON p_partkey = l_partkey AND l_receiptdate > l_commitdate
WHERE p_size IN (29, 34, 36, 19)
GROUP BY p_size
ORDER BY m0 DESC, psize
