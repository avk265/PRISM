-- generated TPC-H-schema training query (seed 7, #180, family subquery); not an official TPC-H query
SELECT SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, part
WHERE p_partkey = l_partkey
  AND p_type LIKE '%BRASS'
  AND l_quantity < (SELECT 0.2 * AVG(l_quantity) FROM lineitem WHERE l_partkey = p_partkey)
