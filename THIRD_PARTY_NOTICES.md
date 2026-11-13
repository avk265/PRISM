# Third-party material

The upstream PRISM package declared MIT licensing; this repository preserves that code-license choice. The manuscript remains the work of its named authors. It is not relicensed by the software notice.

The generated TPC-H data and SQL are benchmark inputs, not independently authored application source. Their provenance and generator commit are recorded in `data/tpch_sf10/manifest.json`. TPC and TPC-H are names of the Transaction Processing Performance Council. These research measurements are not represented as an audited TPC-H performance result. No TPC-H generator source or binary is bundled.

The numerical evidence snapshot's measurements, tables and plots support the supplied manuscript. Earlier manuscript-layout class/style files are not included.

Apache Spark, OpenJDK, NumPy, pandas, scikit-learn, SciPy, XGBoost, LightGBM, Matplotlib, Joblib, Pydantic and psutil retain their respective upstream licenses. Their binaries are installed as dependencies, not copied into this repository. Ernest-, CherryPick-, Lyu- and RIOS-named baselines are local adaptations described in the paper; code from those external research repositories is not bundled as if reproduced faithfully.
