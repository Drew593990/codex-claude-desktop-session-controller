"""Review exactly the Git index; print findings without printing matched values."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT_FILES={'README.md','README.zh-CN.md','LICENSE','SECURITY.md','CONTRIBUTING.md',
    'requirements.txt','.gitignore','.gitattributes','bridge.py','client.py',
    'native-controller.cjs','native-controller.test.cjs','test_bridge.py'}
ROOT_DIRS={'docs','scripts','tests','templates','skill-template','.github'}
PRIVATE_PARTS={'.bridge','.claude','.test-runs','backups','__pycache__','.venv'}
PRIVATE_FILES={'.mcp.json','.session-controller-install.json','auth.json','config.toml','.env'}
PATTERNS={
    'personal Windows user path':re.compile(r'[A-Za-z]:(?:\\+|/)Users(?:\\+|/)[^<\s]+',re.I),
    'developer-specific absolute path':re.compile(r'[A-Za-z]:(?:\\+|/)(?:codex|python|Programs)(?:\\+|/)',re.I),
    'possible API credential':re.compile(r'(?:sk-|gh[pousr]_|github_pat_)[A-Za-z0-9_-]{24,}'),
    'private key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'live Desktop host identifier':re.compile(r'local_[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}',re.I),
}

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL)

def check(root):
    names=[x for x in git(root,'ls-files','-z').decode('utf-8').split('\0') if x]
    findings=[]
    if not names:
        return ['No staged/tracked files to review']
    for name in names:
        parts=Path(name).parts
        if (any(p in PRIVATE_PARTS for p in parts) or Path(name).name in PRIVATE_FILES
                or name.endswith(('.jsonl','.key','.log')) or '.backup-' in name):
            findings.append(f'{name}: private runtime asset')
            continue
        if not (name in ROOT_FILES or parts[0] in ROOT_DIRS):
            findings.append(f'{name}: file outside release allowlist')
            continue
        modes=git(root,'ls-files','-s','--',name).decode('utf-8').split()
        if not modes or modes[0] not in ('100644','100755'):
            findings.append(f'{name}: non-regular index entry')
            continue
        data=git(root,'show',':'+name)
        try:
            text=data.decode('utf-8')
        except UnicodeDecodeError:
            findings.append(f'{name}: unexpected binary asset')
            continue
        for label,pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f'{name}: {label}')
    return findings

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    try:
        findings=check(args.root)
    except subprocess.CalledProcessError:
        parser.exit(1,'Cannot inspect Git index\n')
    if findings:
        print('\n'.join(findings))
        raise SystemExit(1)
    print('Git-index privacy/allowlist check passed; matched values are never printed.')
