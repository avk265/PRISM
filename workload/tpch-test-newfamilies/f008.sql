-- generated TPC-H-schema test-only query (seed 23, #8, family self_join); not an official TPC-H query
WITH m AS (SELECT l_orderkey AS ok, COUNT(DISTINCT l_suppkey) AS ns FROM lineitem GROUP BY l_orderkey HAVING COUNT(DISTINCT l_suppkey) > 2)
SELECT l_shipmode AS sm, COUNT(*) AS m0, SUM(l_extendedprice) AS m1, AVG(ns) AS m2
FROM lineitem, m
WHERE l_orderkey = m.ok
  AND l_receiptdate > l_commitdate
GROUP BY l_shipmode
ORDER BY sm
