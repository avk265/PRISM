-- generated TPC-H-schema training query (seed 7, #327, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0
FROM lineitem, partsupp
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_discount BETWEEN 0.02 AND 0.08
