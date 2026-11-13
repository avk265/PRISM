-- generated TPC-H-schema training query (seed 7, #151, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_orderpriority IN ('1-URGENT', '3-MEDIUM', '2-HIGH')
  AND o_orderstatus = 'P'
ORDER BY custkey, orderpriority
LIMIT 100
