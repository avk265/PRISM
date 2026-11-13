-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0
FROM lineitem
WHERE l_quantity < 25
