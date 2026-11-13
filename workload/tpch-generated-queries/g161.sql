-- generated TPC-H-schema training query (seed 7, #161, family spj_agg); not an official TPC-H query
SELECT o_orderstatus AS orderstatus,
       c_custkey AS c_custkey,
       COUNT(DISTINCT o_custkey) AS m0,
       SUM(o_totalprice) AS m1
FROM orders, customer, nation
WHERE o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND o_totalprice > 1000
  AND c_acctbal > 0
  AND n_name IN ('GERMANY', 'FRANCE', 'KENYA', 'UNITED STATES')
GROUP BY o_orderstatus, c_custkey
ORDER BY m0 DESC, orderstatus, c_custkey
LIMIT 100
