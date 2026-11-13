-- qgen variant of official TPC-H q17 (test only)
-- using 253721326 as a seed to the RNG


select
	sum(l_extendedprice) / 7.0 as avg_yearly
from
	lineitem,
	part
where
	p_partkey = l_partkey
	and p_brand = 'Brand#12'
	and p_container = 'SM PKG'
	and l_quantity < (
		select
			0.2 * avg(l_quantity)
		from
			lineitem
		where
			l_partkey = p_partkey
	);
--#SET ROWS_FETCH -1
