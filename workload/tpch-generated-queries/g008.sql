-- generated TPC-H-schema training query (seed 7, #8, family spj_agg); not an official TPC-H query
SELECT COUNT(DISTINCT l_orderkey) AS m0
FROM lineitem, orders, part
WHERE l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1997-01-01'
