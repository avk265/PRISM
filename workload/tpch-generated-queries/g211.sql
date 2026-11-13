-- generated TPC-H-schema training query (seed 7, #211, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_orderdate >= DATE '1995-04-01' AND o_orderdate < DATE '1998-01-01'
  AND o_orderstatus = 'O'
ORDER BY custkey, orderpriority
LIMIT 100
