-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT o_orderstatus AS orderstatus,
       n_name AS nation,
       c_custkey AS c_custkey,
       COUNT(*) AS m0,
       COUNT(DISTINCT o_custkey) AS m1,
       COUNT(*) AS m2
FROM orders, customer, nation
WHERE o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND o_totalprice > 50000
  AND c_acctbal > -500
  AND o_orderkey IN (SELECT l_orderkey FROM lineitem GROUP BY l_orderkey HAVING SUM(l_quantity) > 250)
GROUP BY o_orderstatus, n_name, c_custkey
ORDER BY m0 DESC, orderstatus, nation, c_custkey
LIMIT 100
