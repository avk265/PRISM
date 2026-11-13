-- generated TPC-H-schema training query (seed 7, #147, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       SUM(s_acctbal) AS m1
FROM lineitem, orders, customer, part, supplier, nation, region
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_partkey = p_partkey
  AND l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND l_shipmode IN ('RAIL', 'REG AIR')
  AND r_name = 'ASIA'
  AND p_container LIKE 'MED%'
GROUP BY l_returnflag
ORDER BY m0 DESC, returnflag
LIMIT 100
