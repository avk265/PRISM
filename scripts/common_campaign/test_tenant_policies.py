"""Policy wiring checks without launching a JVM; live canaries remain required."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from spec import CONCURRENT_POLICIES, S2, OUT, plan_at
from tenant_policies import TenantPolicies, hb


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.fv=SimpleNamespace(plan_features=SimpleNamespace(input_size_bytes=1e9,
            estimated_shuffle_bytes=2e8))
        self.bundles={'random_forest_lm':{'stage1':object(),'stage2':object()}}

    def test_all_37_policies_dispatch_and_two_stage_caps_are_real(self):
        self.assertEqual(len(set(CONCURRENT_POLICIES)),25 if plan_at(OUT) else 37)
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            for name in ('ernest','cherrypick'):
                (directory/f'q1_{name}_live.json').write_text(json.dumps({
                    'sql_sha256':hashlib.sha256(b'SELECT 1').hexdigest(),
                    'selected_executors':3,'profiling_core_s':20,
                    'probes':{'1':{'status':'SUCCESS','checksum':'ok','latency_s':10,
                                  'alloc_core_s':20,'alloc_mem_gb_s':15}}}))
            decision=hb.Decision(4,two_stage_model='random_forest_lm')
            with patch.object(hb,'load_bundles',return_value=self.bundles), \
                 patch.object(hb,'PluggableEnhancedDispatcher'), \
                 patch.object(hb,'predict',return_value=(4,2,1536)), \
                 patch.object(hb,'decide',return_value=(decision,{})) as decide:
                all_policies=tuple(dict.fromkeys(CONCURRENT_POLICIES+tuple(f'{strategy}_nocap' for strategy in S2)))
                self.assertEqual(len(all_policies),37)
                for name in all_policies:
                    policy=TenantPolicies(name,directory,directory,directory)
                    n,conf,stage2,profile=policy.choose('q1','SELECT 1',self.fv,2)
                    if name=='spark_dra':
                        self.assertIsNone(n)
                    else:
                        self.assertIn(n,(1,2,3,4))
                    if '_two_stage_' in name:
                        self.assertIsNotNone(stage2)
                        self.assertIs(stage2['bundle'],self.bundles['random_forest_lm']['stage2'])
                        self.assertEqual(stage2['pool'].num_workers,2 if name.endswith('_cap') else 4)
                        self.assertEqual(n,2 if name.endswith('_cap') else 4)
                called={call.args[0] for call in decide.call_args_list}
                self.assertTrue(set(S2).issubset(called))

    def test_profile_wrong_sql_and_failed_probe_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            source=directory/'q1_ernest_live.json'
            profile={'sql_sha256':'wrong','probes':{'1':{'status':'ERROR'}}}
            source.write_text(json.dumps(profile))
            policy=TenantPolicies('ernest_profiled',directory,directory,directory)
            with self.assertRaisesRegex(RuntimeError,'SQL differs'):
                policy.choose('q1','SELECT 1',self.fv,2)
            profile['sql_sha256']=hashlib.sha256(b'SELECT 1').hexdigest()
            source.write_text(json.dumps(profile))
            with self.assertRaisesRegex(RuntimeError,'Incomplete real profiling'):
                policy.choose('q1','SELECT 1',self.fv,2)

    def test_missing_stage2_bundle_is_not_silently_stage1(self):
        with patch.object(hb,'load_bundles',return_value={'ridge':{'stage2':None}}), \
             patch.object(hb,'decide',return_value=(hb.Decision(3,two_stage_model='ridge'),{})):
            policy=TenantPolicies('prism_ridge_two_stage_cap','.','.','.')
            with self.assertRaisesRegex(RuntimeError,'no trained Stage 2'):
                policy.choose('q1','SELECT 1',self.fv,2)


if __name__=='__main__':
    unittest.main()
