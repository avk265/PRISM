-- generated TPC-H-schema training query (seed 7, #224, family spj_agg); not an official TPC-H query
SELECT o_orderstatus AS orderstatus,
       s_suppkey AS s_suppkey,
       year(l_shipdate) AS ship_year,
       COUNT(*) AS m0,
       SUM(l_extendedprice * (1 - l_discount)) AS m1,
       AVG(o_totalprice) AS m2
FROM lineitem, orders, supplier
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND o_orderdate >= DATE '1993-05-01' AND o_orderdate < DATE '1996-01-01'
  AND s_acctbal > 5000
GROUP BY o_orderstatus, s_suppkey, year(l_shipdate)
ORDER BY m0 DESC, orderstatus, s_suppkey, ship_year
LIMIT 100
