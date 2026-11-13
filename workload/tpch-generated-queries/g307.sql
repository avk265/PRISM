-- generated TPC-H-schema training query (seed 7, #307, family distinct); not an official TPC-H query
SELECT DISTINCT o_custkey AS custkey, o_orderpriority AS orderpriority
FROM orders
WHERE o_totalprice > 50000
  AND o_orderdate >= DATE '1992-04-01' AND o_orderdate < DATE '1997-01-01'
ORDER BY custkey, orderpriority
LIMIT 100
