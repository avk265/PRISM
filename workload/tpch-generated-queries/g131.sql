-- generated TPC-H-schema training query (seed 7, #131, family spj_agg); not an official TPC-H query
SELECT o_orderpriority AS orderpriority,
       o_orderstatus AS orderstatus,
       COUNT(*) AS m0
FROM orders
WHERE o_totalprice > 150000
GROUP BY o_orderpriority, o_orderstatus
ORDER BY m0 DESC, orderpriority, orderstatus
LIMIT 100
