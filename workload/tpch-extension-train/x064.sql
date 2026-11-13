-- generated TPC-H-schema training query (seed 11, #64, family outer_join); not an official TPC-H query
SELECT s_nationkey AS nk, COUNT(l_orderkey) AS m0, SUM(l_extendedprice) AS m1
FROM supplier LEFT OUTER JOIN lineitem ON s_suppkey = l_suppkey AND l_discount BETWEEN 0.02 AND 0.1
GROUP BY s_nationkey
ORDER BY m0 DESC, nk
