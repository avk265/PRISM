-- generated TPC-H-schema training query (seed 11, #55, family outer_join); not an official TPC-H query
SELECT p_size AS psize, COUNT(l_orderkey) AS m0, SUM(l_quantity) AS m1
FROM part LEFT OUTER JOIN lineitem ON p_partkey = l_partkey AND l_discount BETWEEN 0.05 AND 0.1
WHERE p_type LIKE '%NICKEL'
GROUP BY p_size
ORDER BY m0 DESC, psize
