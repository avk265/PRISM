-- generated TPC-H-schema training query (seed 7, #267, family spj_agg); not an official TPC-H query
SELECT SUM(c_acctbal) AS m0,
       COUNT(*) AS m1,
       SUM(o_totalprice) AS m2
FROM orders, customer, lineitem, supplier, nation, part, region
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND l_partkey = p_partkey
  AND n_regionkey = r_regionkey
  AND n_name IN ('INDIA', 'FRANCE')
  AND l_shipmode IN ('MAIL', 'FOB', 'AIR', 'SHIP')
  AND p_brand = 'Brand#41'
