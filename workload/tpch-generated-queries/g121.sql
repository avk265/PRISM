-- generated TPC-H-schema training query (seed 7, #121, family spj_agg); not an official TPC-H query
SELECT c_custkey AS c_custkey,
       year(o_orderdate) AS order_year,
       o_orderstatus AS orderstatus,
       COUNT(DISTINCT o_custkey) AS m0
FROM orders, customer
WHERE o_custkey = c_custkey
  AND c_mktsegment = 'FURNITURE'
  AND o_orderstatus = 'P'
GROUP BY c_custkey, year(o_orderdate), o_orderstatus
HAVING COUNT(*) > 5
ORDER BY m0 DESC, c_custkey, order_year, orderstatus
LIMIT 100
