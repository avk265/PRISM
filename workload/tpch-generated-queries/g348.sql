-- generated TPC-H-schema training query (seed 7, #348, family spj_agg); not an official TPC-H query
SELECT c_custkey AS c_custkey,
       SUM(c_acctbal) AS m0
FROM orders, customer
WHERE o_custkey = c_custkey
  AND c_acctbal > 8000
  AND o_totalprice > 150000
GROUP BY c_custkey
ORDER BY m0 DESC, c_custkey
LIMIT 100
