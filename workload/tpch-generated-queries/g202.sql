-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0,
       COUNT(DISTINCT o_custkey) AS m1,
       AVG(l_discount) AS m2
FROM lineitem, part, orders, supplier, customer, nation, region
WHERE l_partkey = p_partkey
  AND l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND r_name = 'AMERICA'
