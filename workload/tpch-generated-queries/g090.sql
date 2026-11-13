-- generated TPC-H-schema training query (seed 7, #90, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_totalprice > 1000
ORDER BY custkey, orderpriority
LIMIT 100
