"""Exercise actual profiler dispatch with mocked Spark execution, never a JVM."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import live_extensions as extension


class ProfileTests(unittest.TestCase):
    def execute(self,directory,fail=False):
        state={'n':None,'calls':[]}
        fv=SimpleNamespace(query_id='q1')
        pool=SimpleNamespace(executor_cores=2,executor_memory_mb=1536)
        ref=directory/'checksums.json';ref.write_text('{"q1":"good"}')
        args=['trial','--profile-dir',str(directory/'profiles'),'--reference-checksums',str(ref)]
        def set_pool(spark,n):
            state['n']=n
        def run_once(*args,**kwargs):
            n=state['n'];state['calls'].append(n)
            return {'status':'ERROR' if fail else 'SUCCESS','checksum':'good',
                    'latency_s':100/n,'alloc_core_s':200,'alloc_mem_gb_s':150,'executor_cpu_s':100}
        def harness(argv):
            extension.hb.extract_submission_features(None,object())
            state['decision'],_=extension.hb.decide('ernest_live',fv,'SELECT 1',{},None,pool)
            # Resume must reuse real successful probes, not charge/rerun them twice.
            extension.hb.decide('ernest_live',fv,'SELECT 1',{},None,pool)
        with patch.object(sys,'argv',args), \
             patch.object(extension.hb,'extract_submission_features',return_value=fv), \
             patch.object(extension.hb,'set_pool',side_effect=set_pool), \
             patch.object(extension.hb,'run_once',side_effect=run_once), \
             patch.object(extension.hb,'decide'), \
             patch.object(extension.hb,'StandaloneCluster'), \
             patch.object(extension.hb,'main',side_effect=harness):
            extension.main()
        return state

    def test_ernest_executes_real_probe_callbacks_and_preserves_cost(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            result=self.execute(directory)
            self.assertEqual(result['calls'],[1,4])
            self.assertIn(result['decision'].num_executors,(1,2,3,4))
            profile=json.loads((directory/'profiles/q1_ernest_live.json').read_text())
            self.assertEqual(profile['profiling_core_s'],400)
            self.assertEqual(len(profile['attempts']),2)

    def test_profile_failure_is_not_replaced_with_a_fabricated_latency(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)
            with self.assertRaisesRegex(RuntimeError,'Profiling failed'):
                self.execute(directory,fail=True)
            profile=json.loads((directory/'profiles/q1_ernest_live.json').read_text())
            self.assertEqual(profile['attempts'][0]['status'],'ERROR')
            self.assertNotIn('selected_executors',profile)


class JointDispatchTests(unittest.TestCase):
    def execute(self,directory,shape):
        path=directory/'choices.json'
        path.write_text(json.dumps({'q1':{'joint_joint_ridge':[2,1,1024]}}))
        features=SimpleNamespace(input_size_bytes=1e9,join_order_depth=2,
            estimated_shuffle_bytes=1e8,stage_dag_depth=3,stage_dag_branch_factor=2)
        fv=SimpleNamespace(query_id='q1',plan_features=features)
        pool=SimpleNamespace(executor_cores=1,executor_memory_mb=1024)
        model=SimpleNamespace(shapes=[(2,1,1024),(3,1,1024),(4,2,1536)],choose=MagicMock(return_value=shape))
        result={}
        def harness(argv):
            result['decision'],result['meta']=extension.hb.decide('joint_joint_ridge',fv,'SELECT 1',{},None,pool)
        with patch.object(sys,'argv',['trial','--joint-choices',str(path)]), \
             patch.object(extension.hb,'extract_submission_features'), \
             patch.object(extension.hb,'decide'),patch.object(extension.hb,'StandaloneCluster'), \
             patch.object(extension.hb,'main',side_effect=harness), \
             patch('joblib.load',return_value=model):
            extension.main()
        return result,model

    def test_live_predictor_is_called_not_precomputed_executor_lookup(self):
        with tempfile.TemporaryDirectory() as temp:
            result,model=self.execute(Path(temp),(3,1,1024))
            self.assertEqual(result['decision'].num_executors,3)
            model.choose.assert_called_once()
            self.assertIn('live frozen joint predictor',result['meta']['decision_source'])

    def test_different_live_shape_requires_rescheduling_not_wrong_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError,'rescheduling required'):
                self.execute(Path(temp),(4,2,1536))


class BaseDispatchTests(unittest.TestCase):
    def test_base_uses_legacy_bundles_even_in_main_model_load_job(self):
        legacy={'legacy':object()}
        fv=SimpleNamespace(query_id='q1')
        original=MagicMock(return_value=(extension.hb.Decision(2),{}))
        def harness(argv):
            extension.hb.decide('prism_pluggable_enhanced',fv,'SELECT 1',{'main':object()},None,None)
        with patch.object(sys,'argv',['trial','--base-models-dir','legacy-models']), \
             patch.object(extension.hb,'extract_submission_features'), \
             patch.object(extension.hb,'decide',original), \
             patch.object(extension.hb,'load_bundles',return_value=legacy), \
             patch.object(extension.hb,'StandaloneCluster'), \
             patch.object(extension.hb,'Stage2Monitor'), \
             patch.object(extension.hb,'main',side_effect=harness):
            extension.main()
        self.assertIs(original.call_args.args[3],legacy)


if __name__=='__main__':
    unittest.main()
