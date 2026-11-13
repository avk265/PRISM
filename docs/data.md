# Input data and query populations

Only TPC-H SF10 is used by the supplied paper. The original formatted input had eight tables, 91 Parquet files, and 3,447,837,229 compressed bytes. The scale factor describes the generated benchmark scale; the compressed byte count is not 10 GB. Large input files are intentionally excluded from Git.

`data/tpch_sf10/manifest.json` lists every original relative path, SHA256 and byte count. The manifest also records the generator revision and import command. `schema.json` records the exact typed schema and `expected_rows.json` the eight verified SF10 row counts. `python tools/dataset.py describe` prints provenance. If you have an exact copy of the original formatted inputs, use `python tools/dataset.py verify --root PATH`.

For fresh measurements, `python tools/rebuild_data.py` prints the generation plan. Add `--execute` to fetch `gregrahn/tpch-kit` at commit `852ad0a5ee31ebefeed884cea4188781dd9613a3`, build dbgen, generate SF10, and invoke the preserved `tools/import_tpch.py`. The importer uses the original typed columns, including decimal and date types. The wrapper checks all eight table row counts and writes a new receipt without modifying the original manifest. Supply `--raw-dir PATH` to import a complete existing eight-table flat-file set instead of generating one.

Rebuilding has not been represented as another run of the published experiment. Generated rows follow the recorded generator revision and scale, but Spark partitioning, compression metadata, filenames and file hashes can differ. Exact original-byte verification and a schema/row-count-validated rebuild are distinct operations. The paper's results can be audited from the bundled measurements without either operation.

| Split/cohort | SQL IDs | Directory |
|---|---:|---|
| Initial training | 360 | `workload/tpch-generated-queries` |
| Training extension | 120 | `workload/tpch-extension-train` |
| Official evaluation | 22 | `workload/tpch-queries` |
| Parameter variants A | 44 | `workload/tpch-test-qgen-variants` |
| Parameter variants B | 44 | `workload/tpch-test-qgen-variants2` |
| New families | 40 | `workload/tpch-test-newfamilies` |

Training totals 480 instances from 14 generated families. The nominal test inventory contains 150 IDs; the paper's completed broad idle comparison uses 97 common IDs. The official comparison uses all 22 official queries. `configs/query_populations.json` and the archived SLA scope audit specify exact membership and repetition patterns.

The live/tenant catalogue is `q6,q8,v09_2,v19_2,w13_2,w21_2,f008,f039`. Two queries from each of four cohorts were selected using the predeclared content-hash rule recorded in `query_selection_plan.json`. The same catalogue is used across loads and tenant counts. No test timing selects a training margin or the primary learner.

The stored SQL and its identifiers are preserved exactly. Do not deduplicate, change query text, increase the test count, or substitute TPC-DS and then present the original paper's tables as results of that altered protocol.
