-- generated TPC-H-schema training query (seed 7, #287, family subquery); not an official TPC-H query
SELECT SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, part
WHERE p_partkey = l_partkey
  AND p_size IN (45, 36, 21, 44, 42, 29, 49)
  AND l_quantity < (SELECT 0.2 * AVG(l_quantity) FROM lineitem WHERE l_partkey = p_partkey)
