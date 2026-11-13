-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT o_orderstatus AS orderstatus,
       SUM(c_acctbal) AS m0,
       SUM(o_totalprice) AS m1
FROM orders, customer, nation, region
WHERE o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND r_name = 'AFRICA'
  AND o_orderdate >= DATE '1995-02-01' AND o_orderdate < DATE '1995-01-01'
  AND c_acctbal > 3000
GROUP BY o_orderstatus
ORDER BY m0 DESC, orderstatus
LIMIT 100
