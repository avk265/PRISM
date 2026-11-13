-- generated TPC-H-schema training query (seed 11, #69, family outer_join); not an official TPC-H query
SELECT p_size AS psize, COUNT(l_orderkey) AS m0, SUM(l_quantity) AS m1
FROM part LEFT OUTER JOIN lineitem ON p_partkey = l_partkey AND l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1999-01-01'
WHERE p_brand = 'Brand#44'
GROUP BY p_size
ORDER BY m0 DESC, psize
