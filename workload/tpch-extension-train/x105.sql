-- generated TPC-H-schema training query (seed 11, #105, family window); not an official TPC-H query
WITH s AS (SELECT l_suppkey AS sk, year(l_shipdate) AS yr, SUM(l_extendedprice * (1 - l_discount)) AS rev
           FROM lineitem
WHERE l_shipmode IN ('FOB', 'REG AIR', 'AIR', 'RAIL') GROUP BY l_suppkey, year(l_shipdate)),
     w AS (SELECT sk, yr, rev, RANK() OVER (PARTITION BY yr ORDER BY rev DESC, sk) AS rk FROM s)
SELECT yr, sk, rev AS m0 FROM w WHERE rk <= 10
ORDER BY yr, m0 DESC, sk
