-- generated TPC-H-schema training query (seed 7, #46, family spj_agg); not an official TPC-H query
SELECT SUM(l_quantity) AS m0
FROM lineitem, supplier, orders, part, nation
WHERE l_suppkey = s_suppkey
  AND l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND s_nationkey = n_nationkey
  AND s_acctbal > -500
  AND n_name IN ('JAPAN', 'PERU', 'CHINA', 'GERMANY')
