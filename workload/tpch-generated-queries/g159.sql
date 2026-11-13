-- generated TPC-H-schema training query (seed 7, #159, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_orderpriority IN ('4-NOT SPECIFIED')
ORDER BY custkey, orderpriority
LIMIT 100
