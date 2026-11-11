import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class PublicScanTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.test-runs').mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'.test-runs')
        self.repo=Path(self.tmp.name)
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
    def tearDown(self):
        self.tmp.cleanup()
    def stage(self,name,text):
        target=self.repo/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(text,encoding='utf-8')
        subprocess.run(['git','-C',str(self.repo),'add','-f','--',name],check=True,capture_output=True)
    def scan(self):
        return subprocess.run([sys.executable,'-B',str(ROOT/'scripts/check_public.py'),'--root',str(self.repo)],
            capture_output=True,text=True,encoding='utf-8')
    def test_clean_tracked_source_passes(self):
        self.stage('README.md','Generic installation guidance.\n')
        self.assertEqual(self.scan().returncode,0)
    def test_forced_runtime_file_fails(self):
        self.stage('.bridge/runtime.json','{}')
        result=self.scan()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('runtime',result.stdout.lower())
    def test_secret_value_fails_without_echoing_value(self):
        value='sk-'+'x'*40
        self.stage('README.md',value)
        result=self.scan()
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn(value,result.stdout+result.stderr)
        self.assertIn('credential',result.stdout.lower())
    def test_personal_user_path_fails(self):
        value='C:'+chr(92)+'Users'+chr(92)+'someone-private'+chr(92)+'file'
        self.stage('README.md',value)
        result=self.scan()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('personal',result.stdout.lower())

if __name__=='__main__':
    unittest.main()
