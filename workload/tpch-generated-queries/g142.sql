-- generated TPC-H-schema training query (seed 7, #142, family cte); not an official TPC-H query
WITH a AS (SELECT o_custkey AS ck, SUM(o_totalprice) AS spend FROM orders
WHERE o_orderpriority IN ('3-MEDIUM', '2-HIGH') GROUP BY o_custkey),
     b AS (SELECT c_custkey AS ck, c_nationkey AS nk FROM customer)
SELECT n_name AS nation, COUNT(*) AS m0, SUM(spend) AS m1
FROM a, b, nation
WHERE a.ck = b.ck AND b.nk = n_nationkey
GROUP BY n_name
ORDER BY m1 DESC, nation
