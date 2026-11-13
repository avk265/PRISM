-- generated TPC-H-schema training query (seed 7, #247, family case); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       SUM(CASE WHEN o_orderpriority IN ('1-URGENT', '2-HIGH') THEN 1 ELSE 0 END) AS m0,
       SUM(CASE WHEN o_orderpriority NOT IN ('1-URGENT', '2-HIGH') THEN 1 ELSE 0 END) AS m1
FROM orders, lineitem
WHERE o_orderkey = l_orderkey
  AND l_shipmode IN ('TRUCK', 'RAIL')
  AND l_quantity < 5
GROUP BY l_shipmode
ORDER BY shipmode
