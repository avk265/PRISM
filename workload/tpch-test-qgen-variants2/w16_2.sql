-- qgen variant of official TPC-H q16 (test only, second variant set)
-- using 410664859 as a seed to the RNG


select
	p_brand,
	p_type,
	p_size,
	count(distinct ps_suppkey) as supplier_cnt
from
	partsupp,
	part
where
	p_partkey = ps_partkey
	and p_brand <> 'Brand#13'
	and p_type not like 'STANDARD BRUSHED%'
	and p_size in (3, 42, 7, 50, 47, 41, 13, 46)
	and ps_suppkey not in (
		select
			s_suppkey
		from
			supplier
		where
			s_comment like '%Customer%Complaints%'
	)
group by
	p_brand,
	p_type,
	p_size
order by
	supplier_cnt desc,
	p_brand,
	p_type,
	p_size;
--#SET ROWS_FETCH -1
