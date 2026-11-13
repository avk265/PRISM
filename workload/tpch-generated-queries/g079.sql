-- generated TPC-H-schema training query (seed 7, #79, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_orderpriority IN ('2-HIGH', '1-URGENT', '5-LOW')
  AND o_totalprice > 150000
ORDER BY custkey, orderpriority
LIMIT 100
