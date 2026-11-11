"""Generate local workspace/skill configuration; no network or model calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'codex-claude-desktop-session-controller'
ASSETS = ('bridge.py', 'client.py', 'native-controller.cjs')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def read_json(file, default):
    return json.loads(file.read_text(encoding='utf-8-sig')) if file.exists() else default

def queue_write(changes, file, data, backup=False):
    if file.is_symlink():
        raise ValueError(f'Refusing symbolic-link destination: {file.name}')
    parent = file.parent
    while parent != parent.parent:
        if parent.is_symlink() or (hasattr(parent,'is_junction') and parent.is_junction()):
            raise ValueError('Refusing linked destination ancestor')
        parent = parent.parent
    if file.exists() and not file.is_file():
        raise ValueError(f'Destination is not a regular file: {file.name}')
    if not file.exists() or file.read_bytes() != data:
        changes.append((file,data,backup))

def install(workspace, codex_home, python, node, register=False):
    workspace, codex_home = workspace.resolve(), codex_home.resolve()
    if workspace == Path(workspace.anchor) or workspace == ROOT:
        raise ValueError('Choose a dedicated bridge workspace, not the source checkout or a filesystem root')
    python = str(Path(python).resolve())
    node_path = shutil.which(node)
    if not node_path:
        raise ValueError('Node was not found; supply --node PATH')
    if not Path(python).is_file():
        raise ValueError('Python executable was not found')
    skill = codex_home / 'skills' / SLUG
    marker = workspace / '.session-controller-install.json'
    old = read_json(marker, {'files':{}})
    if not isinstance(old,dict) or not isinstance(old.get('files'),dict):
        raise ValueError('Invalid previous installation manifest')
    changes, managed = [], {}
    rendered = {
        'bridge.py': (ROOT/'bridge.py').read_bytes(),
        'client.py': (ROOT/'client.py').read_bytes(),
        'native-controller.cjs': (ROOT/'native-controller.cjs').read_bytes(),
        'CLAUDE.md': (ROOT/'templates/controller-CLAUDE.md').read_bytes(),
    }
    replacements = {
        '@@WORKSPACE@@':str(workspace), '@@PYTHON@@':python, '@@NODE@@':node_path,
        '@@WORKSPACE_PS@@':"'"+str(workspace).replace("'","''")+"'",
        '@@PYTHON_PS@@':"'"+python.replace("'","''")+"'",
        '@@NODE_PS@@':"'"+node_path.replace("'","''")+"'",
    }
    for source in (ROOT/'skill-template').rglob('*'):
        if not source.is_file():
            continue
        content = source.read_text(encoding='utf-8')
        for key,value in replacements.items():
            content=content.replace(key,value)
        destination=skill/source.relative_to(ROOT/'skill-template')
        rendered[destination]=content.encode('utf-8')
    for relative,data in rendered.items():
        destination = workspace/relative if isinstance(relative,str) else relative
        key = str(destination)
        if destination.exists() and destination.read_bytes()!=data:
            if old['files'].get(key)!=digest(destination.read_bytes()):
                raise ValueError(f'Refusing to overwrite edited/unmanaged file: {destination.name}')
        queue_write(changes,destination,data,True)
        managed[key]=digest(data)
    mcp_file=workspace/'.mcp.json'
    mcp=read_json(mcp_file, {})
    if not isinstance(mcp,dict) or not isinstance(mcp.get('mcpServers',{}),dict):
        raise ValueError('Invalid project .mcp.json')
    server={'command':python,'args':['-B','-X','utf8',str(workspace/'bridge.py')],
            'timeout':3700000}
    existing=mcp.setdefault('mcpServers',{}).get('codex_bridge')
    if existing is not None and existing!=server:
        if not (marker.exists() and old['files'].get(str(mcp_file))==digest(mcp_file.read_bytes())):
            raise ValueError('Conflicting codex_bridge MCP server; existing configuration preserved')
    mcp['mcpServers']['codex_bridge']=server
    mcp_data=json_bytes(mcp)
    queue_write(changes,mcp_file,mcp_data,True)
    managed[str(mcp_file)]=digest(mcp_data)
    if register:
        config=codex_home/'config.toml'
        text=config.read_text(encoding='utf-8-sig') if config.exists() else ''
        parsed=tomllib.loads(text)
        entries=parsed.get('skills',{}).get('config',[])
        found=[e for e in entries if e.get('path')==str(skill/'SKILL.md')]
        if found and (len(found)!=1 or found[0].get('enabled') is False):
            raise ValueError('Skill has an existing disabled/duplicate configuration; resolve it explicitly')
        if not found:
            text+='\n[[skills.config]]\npath = '+json.dumps(str(skill/'SKILL.md'),ensure_ascii=False)+'\nenabled = true\n'
        tomllib.loads(text)
        queue_write(changes,config,text.encode('utf-8'),True)
        rules=codex_home/'AGENTS.md'
        text=rules.read_text(encoding='utf-8-sig') if rules.exists() else ''
        begin,end=f'<!-- {SLUG}:begin -->',f'<!-- {SLUG}:end -->'
        rule=(f'{begin}\nWhen collaborating with Claude Desktop Code, read `{skill / "SKILL.md"}`. '
              f'Create new work sessions in `{workspace}` by default. Explicitly selected existing sessions '
              'may be in other project folders; preserve their ID, directory and history. '
              'Continue the same session for follow-ups. Use native peer/controller tools, not hidden model CLI tasks or GUI automation.\n'+end)
        if begin in text or end in text:
            if text.count(begin)!=1 or text.count(end)!=1 or text.index(begin)>text.index(end):
                raise ValueError('Invalid existing controller rule markers')
            a,b=text.index(begin),text.index(end)+len(end)
            text=text[:a]+rule+text[b:]
        else:
            text=text.rstrip()+'\n\n'+rule+'\n'
        queue_write(changes,rules,text.encode('utf-8'),True)
    queue_write(changes,marker,json_bytes({'version':1,'files':managed}))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    for file,data,backup in changes:
        file.parent.mkdir(parents=True,exist_ok=True)
        if backup and file.exists():
            shutil.copy2(file,file.with_name(file.name+'.backup-'+stamp))
        temporary=file.with_name(file.name+'.install-tmp-'+stamp)
        with temporary.open('xb') as stream:
            stream.write(data)
        os.replace(temporary,file)
    return {'workspace':str(workspace),'skill':str(skill/'SKILL.md'),'registered':register,
            'files_changed':len(changes),'models_started':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--codex-home',type=Path,default=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))))
    parser.add_argument('--python',default=sys.executable)
    parser.add_argument('--node',default='node')
    parser.add_argument('--register',action='store_true',help='Back up and add this skill to Codex config and global rules')
    args=parser.parse_args()
    try:
        print(json.dumps(install(args.workspace,args.codex_home,args.python,args.node,args.register),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as error:
        parser.exit(1,str(error)+'\n')
