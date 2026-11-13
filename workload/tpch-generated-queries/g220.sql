-- generated TPC-H-schema training query (seed 7, #220, family spj_agg); not an official TPC-H query
SELECT AVG(l_discount) AS m0,
       COUNT(*) AS m1,
       COUNT(*) AS m2
FROM lineitem, supplier, nation, orders
WHERE l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND l_orderkey = o_orderkey
  AND s_acctbal > -500
  AND o_totalprice > 1000
  AND n_name IN ('FRANCE', 'UNITED STATES')
