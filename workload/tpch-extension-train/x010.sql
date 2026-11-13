-- generated TPC-H-schema training query (seed 11, #10, family outer_join); not an official TPC-H query
SELECT c_mktsegment AS seg, COUNT(o_orderkey) AS m0, COUNT(*) AS m1, SUM(o_totalprice) AS m2
FROM customer LEFT OUTER JOIN orders ON c_custkey = o_custkey AND o_orderdate >= DATE '1994-04-01' AND o_orderdate < DATE '1996-01-01'
GROUP BY c_mktsegment
ORDER BY m0 DESC, seg
