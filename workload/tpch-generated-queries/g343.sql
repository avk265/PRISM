-- generated TPC-H-schema training query (seed 7, #343, family spj_agg); not an official TPC-H query
SELECT o_orderpriority AS orderpriority,
       AVG(o_totalprice) AS m0
FROM orders, customer, nation, region
WHERE o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND n_name IN ('PERU')
  AND o_totalprice > 50000
GROUP BY o_orderpriority
ORDER BY m0 DESC, orderpriority
LIMIT 100
