-- generated TPC-H-schema training query (seed 7, #84, family spj_agg); not an official TPC-H query
SELECT SUM(l_extendedprice * (1 - l_discount)) AS m0
FROM lineitem
WHERE l_quantity < 5
