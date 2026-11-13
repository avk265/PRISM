-- generated TPC-H-schema training query (seed 7, #273, family case); not an official TPC-H query
SELECT l_shipmode AS shipmode,
       SUM(CASE WHEN o_orderpriority IN ('1-URGENT', '2-HIGH') THEN 1 ELSE 0 END) AS m0,
       SUM(CASE WHEN o_orderpriority NOT IN ('1-URGENT', '2-HIGH') THEN 1 ELSE 0 END) AS m1
FROM orders, lineitem
WHERE o_orderkey = l_orderkey
  AND l_quantity < 25
  AND l_receiptdate > l_commitdate
GROUP BY l_shipmode
ORDER BY shipmode
