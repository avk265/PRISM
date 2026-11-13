-- generated TPC-H-schema training query (seed 7, #37, family semi_anti); not an official TPC-H query
SELECT p_brand AS brand, COUNT(*) AS m0, AVG(p_retailprice) AS m1
FROM part
WHERE p_container LIKE 'JUMBO%'
  AND EXISTS (SELECT 1 FROM lineitem WHERE l_partkey = p_partkey AND l_shipdate >= DATE '1992-01-01' AND l_shipdate < DATE '1999-01-01')
GROUP BY p_brand
ORDER BY m0 DESC, brand
LIMIT 100
