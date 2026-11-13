-- generated TPC-H-schema training query (seed 7, #101, family spj_agg); not an official TPC-H query
SELECT MAX(l_extendedprice) AS m0,
       SUM(l_quantity) AS m1,
       COUNT(DISTINCT l_orderkey) AS m2
FROM lineitem, part
WHERE l_partkey = p_partkey
  AND l_shipdate >= DATE '1992-01-01' AND l_shipdate < DATE '1995-01-01'
  AND p_size IN (48, 3)
