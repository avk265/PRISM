-- generated TPC-H-schema training query (seed 7, #39, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       year(l_shipdate) AS ship_year,
       AVG(l_discount) AS m0
FROM lineitem, orders, customer, part, supplier, partsupp
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_partkey = p_partkey
  AND l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND o_orderdate >= DATE '1994-03-01' AND o_orderdate < DATE '1997-01-01'
GROUP BY p_size, year(l_shipdate)
HAVING COUNT(*) > 5
ORDER BY m0 DESC, psize, ship_year
LIMIT 100
