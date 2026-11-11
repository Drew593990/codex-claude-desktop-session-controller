"""Exercise generated installs, not just the installer source text."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]

class InstallTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.test-runs').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '.test-runs')
        self.base = Path(self.tmp.name)
        self.workspace = self.base / "团队's bridge project"
        self.codex = self.base / 'custom codex home'
        self.workspace.mkdir()
        self.codex.mkdir()
        (self.workspace / '.mcp.json').write_text(json.dumps({'mcpServers':{'existing':{'command':'unchanged'}}}), encoding='utf-8')
        (self.codex / 'config.toml').write_text('model = "keep-this"\n', encoding='utf-8')
        (self.codex / 'AGENTS.md').write_text('Keep my research rules.\n', encoding='utf-8')
    def tearDown(self):
        self.tmp.cleanup()
    def install(self, *extra):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', RELEASE_TEST_SECRET='never-export-environment-values')
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT/'scripts/install.py'),
            '--workspace', str(self.workspace), '--codex-home', str(self.codex), '--register', *extra],
            capture_output=True, text=True, encoding='utf-8', env=env)
    def test_portable_install_preserves_unrelated_settings_and_is_idempotent(self):
        first = self.install()
        self.assertEqual(first.returncode, 0, first.stderr)
        mcp = json.loads((self.workspace/'.mcp.json').read_text(encoding='utf-8'))['mcpServers']
        self.assertEqual(mcp['existing'], {'command':'unchanged'})
        self.assertEqual(mcp['codex_bridge']['command'], sys.executable)
        self.assertEqual(mcp['codex_bridge']['args'][-1], str(self.workspace/'bridge.py'))
        self.assertTrue((self.workspace/'native-controller.cjs').is_file())
        entry = self.codex/'skills/codex-claude-desktop-session-controller/SKILL.md'
        self.assertTrue(entry.is_file())
        body = entry.read_text(encoding='utf-8')
        self.assertIn(str(self.workspace), body)
        self.assertNotIn('@@', body)
        parsed = tomllib.loads((self.codex/'config.toml').read_text(encoding='utf-8'))
        self.assertEqual(parsed['model'], 'keep-this')
        self.assertEqual(parsed['skills']['config'], [{'path':str(entry), 'enabled':True}])
        rules = (self.codex/'AGENTS.md').read_text(encoding='utf-8')
        self.assertTrue(rules.startswith('Keep my research rules.'))
        self.assertTrue(list(self.codex.glob('AGENTS.md.backup-*')))
        self.assertTrue(list(self.codex.glob('config.toml.backup-*')))
        self.assertEqual(self.install().returncode, 0)
        self.assertEqual((self.codex/'AGENTS.md').read_text(encoding='utf-8'), rules)
        for file in self.base.rglob('*'):
            if file.is_file():
                self.assertNotIn('never-export-environment-values', file.read_text(encoding='utf-8'))
    def test_user_edited_managed_file_is_not_overwritten(self):
        self.assertEqual(self.install().returncode, 0)
        target = self.workspace/'bridge.py'
        target.write_text('# my local change\n', encoding='utf-8')
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(encoding='utf-8'), '# my local change\n')
    def test_existing_conflicting_server_is_preserved(self):
        config = {'mcpServers':{'codex_bridge':{'command':'someone-elses-server'}}}
        (self.workspace/'.mcp.json').write_text(json.dumps(config),encoding='utf-8')
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Conflicting',result.stderr)
        self.assertEqual(json.loads((self.workspace/'.mcp.json').read_text()), config)

if __name__ == '__main__':
    (ROOT/'.test-runs').mkdir(exist_ok=True)
    unittest.main()
