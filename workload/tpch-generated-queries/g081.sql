-- generated TPC-H-schema training query (seed 7, #81, family spj_agg); not an official TPC-H query
SELECT p_brand AS brand,
       p_type AS ptype,
       l_shipmode AS shipmode,
       SUM(l_quantity) AS m0,
       SUM(ps_supplycost * ps_availqty) AS m1
FROM lineitem, part, partsupp
WHERE l_partkey = p_partkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_quantity < 40
  AND ps_availqty > 5000
GROUP BY p_brand, p_type, l_shipmode
ORDER BY m0 DESC, brand, ptype, shipmode
LIMIT 100
