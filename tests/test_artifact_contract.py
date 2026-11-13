import importlib.util
import json
import re
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('run_experiments',ROOT/'tools/run_experiments.py');launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)

class ArtifactContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.config=json.loads((ROOT/'configs/experiments.json').read_text())
    def plan(self,study):return list(launcher.jobs(self.config,study,ROOT/'runs/test-plan',ROOT/'data/tpch-10gb-parquet'))
    def test_official_repetition_and_method_count(self):
        jobs=self.plan('official');self.assertEqual(len(jobs),1);args=jobs[0][1]
        self.assertEqual(args[args.index('--reps')+1],'3');self.assertEqual(len(args[args.index('--strategies')+1].split(',')),18)
    def test_live_has_equal_ids_across_all_loads(self):
        jobs=self.plan('live');self.assertEqual(len(jobs),24);loads={}
        for _,args in jobs:
            load=args[args.index('--contention')+1];loads.setdefault(load,set()).add(args[args.index('--queries')+1])
            self.assertEqual(args[args.index('--reps')+1],'1');self.assertEqual(len(args[args.index('--strategies')+1].split(',')),23)
        self.assertEqual(loads['0'],loads['4']);self.assertEqual(loads['4'],loads['8']);self.assertEqual(len(loads['0']),8)
    def test_concurrent_uses_measured_driver_setting_and_23_policies(self):
        _,args=self.plan('concurrency')[0]
        self.assertEqual(args[args.index('--driver-memory')+1],'1g');self.assertEqual(args[args.index('--streams')+1],'1,2,3')
        self.assertEqual(len(args[args.index('--policies')+1].split(',')),23)
    def test_temporary_storage_not_part_of_frozen_data(self):
        self.assertNotIn('proposal_campaign',str(self.plan('all')));self.assertNotIn('tpcds',str(self.plan('all')).lower())
    def test_growth_paths_are_explicit_real_trajectories(self):
        plans=self.plan('growth');self.assertEqual(len(plans),4)
        for _,args in plans:self.assertEqual(len(args[args.index('--strategies')+1].split(',')),6)
    def test_components_cover_both_training_sizes_and_full_cohorts(self):
        plans=self.plan('components');self.assertEqual(len(plans),8)
        for _,args in plans:
            self.assertIn('--no-fallback',args);self.assertEqual(args[args.index('--fb')+1],'none');self.assertIn('--grow',args)
    def test_training_writes_new_model_directory(self):
        plans=self.plan('train');self.assertEqual(len(plans),2)
        self.assertIn('/runs/test-plan/trained_models',plans[0][1][-1])
    def test_reorganized_training_and_component_inputs_exist(self):
        for study in ('train','components'):
            for _,args in self.plan(study):
                for flag in ('--train','--test','--grow','--models'):
                    if flag not in args:continue
                    index=args.index(flag)+1
                    while index<len(args) and not args[index].startswith('--'):
                        path=Path(args[index])
                        if path.is_relative_to(ROOT/'runs'):break
                        self.assertTrue(path.exists(),str(path))
                        if flag in ('--train','--test','--grow'):
                            self.assertTrue((path/'runs.csv').is_file(),str(path))
                        index+=1
    def test_public_tree_excludes_personal_home_paths_and_working_archives(self):
        for path in ROOT.rglob('*'):
            if any(part in path.parts for part in ('.git','.venv','__pycache__','runs')):continue
            self.assertNotEqual(path.name,'results_honest')
            if path.is_dir():
                self.assertIsNone(re.fullmatch(r'v[0-9]+',path.name),str(path))
            elif path.suffix in ('.csv','.json','.md','.py','.txt'):
                self.assertIsNone(re.search(rb'/(?:home|Users)/[A-Za-z0-9_.-]+/',path.read_bytes()),str(path))
    def test_assets_have_unique_names_and_exact_sizes(self):
        m=json.loads((ROOT/'data/tpch_sf10/manifest.json').read_text());self.assertEqual(len(m['files']),91)
        self.assertEqual(len({f['path'] for f in m['files']}),91);self.assertEqual(sum(f['bytes'] for f in m['files']),3447837229)

if __name__=='__main__':unittest.main()
