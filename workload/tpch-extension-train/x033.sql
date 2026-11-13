-- generated TPC-H-schema training query (seed 11, #33, family outer_join); not an official TPC-H query
SELECT p_size AS psize, COUNT(l_orderkey) AS m0, SUM(l_quantity) AS m1
FROM part LEFT OUTER JOIN lineitem ON p_partkey = l_partkey AND l_discount BETWEEN 0.02 AND 0.06
WHERE p_brand = 'Brand#14'
GROUP BY p_size
ORDER BY m0 DESC, psize
