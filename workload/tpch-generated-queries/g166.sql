-- generated TPC-H-schema training query (seed 7, #166, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_orderdate >= DATE '1994-06-01' AND o_orderdate < DATE '1997-01-01'
  AND o_orderpriority IN ('1-URGENT', '3-MEDIUM')
ORDER BY custkey, orderpriority
LIMIT 100
