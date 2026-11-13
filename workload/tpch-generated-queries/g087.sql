-- generated TPC-H-schema training query (seed 7, #87, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_totalprice > 1000
  AND o_orderdate >= DATE '1996-06-01' AND o_orderdate < DATE '1998-01-01'
ORDER BY custkey, orderpriority
LIMIT 100
