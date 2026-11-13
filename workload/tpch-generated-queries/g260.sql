-- generated TPC-H-schema training query (seed 7, #260, family semi_anti); not an official TPC-H query
SELECT p_brand AS brand, COUNT(*) AS m0, AVG(p_retailprice) AS m1
FROM part
WHERE p_size IN (21, 12, 18, 17, 35, 2, 11, 41)
  AND EXISTS (SELECT 1 FROM lineitem WHERE l_partkey = p_partkey AND l_receiptdate > l_commitdate)
GROUP BY p_brand
ORDER BY m0 DESC, brand
LIMIT 100
