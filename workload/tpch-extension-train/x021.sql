-- generated TPC-H-schema training query (seed 11, #21, family outer_join); not an official TPC-H query
SELECT c_mktsegment AS seg, COUNT(o_orderkey) AS m0, COUNT(*) AS m1, SUM(o_totalprice) AS m2
FROM customer LEFT OUTER JOIN orders ON c_custkey = o_custkey
WHERE c_mktsegment = 'FURNITURE'
GROUP BY c_mktsegment
ORDER BY m0 DESC, seg
