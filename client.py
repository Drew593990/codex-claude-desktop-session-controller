"""Codex-side message transport only. Does not launch Claude or call model APIs."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent
OPENER = build_opener(ProxyHandler({}))


def request(runtime, method, path, body=None):
    url = urlparse(runtime["api_url"])
    if url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port:
        raise ValueError("Runtime is not a loopback inbox")
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(runtime["api_url"] + path, data=data, method=method,
                  headers={"Authorization": "Bearer " + runtime["token"],
                           "Content-Type": "application/json"})
    with OPENER.open(req, timeout=5) as response:
        return json.load(response)


def live_instances(directory):
    result = []
    for file in (directory / "instances").glob("*.json"):
        try:
            runtime = json.loads(file.read_text(encoding="utf-8"))
            state = request(runtime, "GET", "/status")
            if state["instance_id"] == runtime["instance_id"]:
                result.append((runtime, state))
        except Exception:
            continue
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "send", "result", "ping"])
    parser.add_argument("--runtime-dir", type=Path, default=ROOT / ".bridge")
    parser.add_argument("--instance")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--task-id")
    args = parser.parse_args()
    instances = live_instances(args.runtime_dir)
    if args.action == "status":
        output = {"connected_inboxes": len(instances), "instances": [s for _, s in instances]}
    else:
        if args.instance:
            instances = [(r, s) for r, s in instances if s["instance_id"] == args.instance]
        if len(instances) != 1:
            parser.exit(2, "Exactly one live desktop inbox is required; select --instance if several are open.\n")
        runtime, state = instances[0]
        if args.action == "result":
            if not args.task_id:
                parser.error("--task-id is required")
            output = request(runtime, "GET", "/tasks/" + args.task_id)
        else:
            if not state["waiting"]:
                parser.exit(2, "The desktop receiver is not waiting. Resume its inbox in Claude Desktop first.\n")
            if args.action == "ping":
                instruction = "连接测试：请在当前 Claude 桌面会话中只回复“桌面原生桥接测试通过”，然后将同样文字用 submit_result 返回。不要读取或修改文件，不要运行命令。"
            else:
                if not args.file:
                    parser.error("--file is required")
                instruction = args.file.read_text(encoding="utf-8-sig")
            output = request(runtime, "POST", "/tasks", {"instruction": instruction})
    print(json.dumps(output, ensure_ascii=False, indent=2))
