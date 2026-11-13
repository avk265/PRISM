-- generated TPC-H-schema training query (seed 11, #11, family big_join); not an official TPC-H query
SELECT o_custkey AS ck, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer, nation
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND o_orderdate >= DATE '1992-01-01' AND o_orderdate < DATE '1993-01-01'
  AND l_discount BETWEEN 0.05 AND 0.1
GROUP BY o_custkey
ORDER BY m0 DESC, ck
LIMIT 100
