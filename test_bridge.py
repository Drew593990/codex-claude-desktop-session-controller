"""Exercise the real MCP stdio connection and the local task transport; no AI calls."""
import asyncio
import json
import sys
import unittest
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent


def http(runtime, method, path, body=None, token=None):
    data = None if body is None else json.dumps(body).encode()
    request = Request(runtime["api_url"] + path, data=data, method=method,
                      headers={"Authorization": "Bearer " + (token or runtime["token"]),
                               "Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return json.load(response)


def payload(result):
    return json.loads(next(block.text for block in result.content if block.type == "text"))


class TracedWriter:
    """Observe real JSON-RPC request IDs without altering messages."""
    def __init__(self, stream):
        self.stream = stream
        self.tool_ids = []

    async def send(self, message):
        root = message.message.root
        if getattr(root, "method", None) == "tools/call":
            self.tool_ids.append(root.id)
        await self.stream.send(message)

    def __getattr__(self, name):
        return getattr(self.stream, name)

    async def __aenter__(self):
        await self.stream.__aenter__()
        return self

    async def __aexit__(self, *args):
        return await self.stream.__aexit__(*args)


class BridgeIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_desktop_mcp_receives_task_and_codex_reads_exact_result(self):
        self.assertTrue((ROOT / "bridge.py").is_file(),
                        "The desktop MCP task bridge has not been implemented")
        runtime_dir = ROOT / ".test-runs" / str(uuid.uuid4())
        params = StdioServerParameters(command=sys.executable,
                                      args=[str(ROOT / "bridge.py"), "--runtime-dir", str(runtime_dir)],
                                      cwd=str(ROOT))
        async with stdio_client(params) as (reader, writer):
            traced = TracedWriter(writer)
            async with ClientSession(reader, traced) as session:
                await session.initialize()
                tools = await session.list_tools()
                self.assertEqual({t.name for t in tools.tools},
                                 {"bridge_status", "wait_for_task", "submit_result"})
                state = payload(await session.call_tool("bridge_status", {}))
                self.assertEqual(state["model_processes_started"], 0)
                runtime = json.loads((runtime_dir / "instances" / (state["instance_id"] + ".json")).read_text())
                with self.assertRaises(HTTPError) as denied:
                    await asyncio.to_thread(http, runtime, "GET", "/status", token="wrong-token")
                self.assertEqual(denied.exception.code, 401)
                interrupted = asyncio.create_task(session.call_tool("wait_for_task", {"timeout_seconds": 5}))
                for _ in range(50):
                    current = await asyncio.to_thread(http, runtime, "GET", "/status")
                    if current["waiting"]:
                        break
                    await asyncio.sleep(0.02)
                self.assertTrue(current["waiting"])
                await session.send_notification(types.ClientNotification(root=types.CancelledNotification(
                    params=types.CancelledNotificationParams(requestId=traced.tool_ids[-1],
                                                             reason="Desktop user interrupted the wait"))))
                interrupted.cancel()
                await asyncio.gather(interrupted, return_exceptions=True)
                for _ in range(50):
                    current = await asyncio.to_thread(http, runtime, "GET", "/status")
                    if not current["waiting"]:
                        break
                    await asyncio.sleep(0.02)
                self.assertFalse(current["waiting"], "An interrupted desktop wait must stop receiving")
                waiting = asyncio.create_task(session.call_tool("wait_for_task", {"timeout_seconds": 5}))
                for _ in range(50):
                    current = await asyncio.to_thread(http, runtime, "GET", "/status")
                    if current["waiting"]:
                        break
                    await asyncio.sleep(0.02)
                self.assertTrue(current["waiting"])
                offered = await asyncio.to_thread(http, runtime, "POST", "/tasks",
                                                 {"instruction": "连接测试：只回复测试文字，不读取文件或运行命令。"})
                received = payload(await waiting)
                self.assertEqual(received["task"]["id"], offered["id"])
                self.assertEqual(received["task"]["instruction"], offered["instruction"])
                invalid = await session.call_tool("submit_result",
                                                 {"task_id": str(uuid.uuid4()), "answer": "wrong", "status": "completed"})
                self.assertTrue(invalid.isError)
                answer = "桌面连接正常：α + β = 1\n第二行保持原样。"
                saved = await session.call_tool("submit_result",
                                               {"task_id": offered["id"], "answer": answer, "status": "completed"})
                self.assertFalse(saved.isError)
                result = await asyncio.to_thread(http, runtime, "GET", "/tasks/" + offered["id"])
                self.assertEqual(result["answer"], answer)
                self.assertEqual(result["status"], "completed")
                duplicate = await session.call_tool("submit_result",
                                                   {"task_id": offered["id"], "answer": "overwrite", "status": "completed"})
                self.assertTrue(duplicate.isError)
                self.assertEqual((await asyncio.to_thread(http, runtime, "GET", "/tasks/" + offered["id"]))["answer"], answer)
                idle = payload(await session.call_tool("wait_for_task", {"timeout_seconds": 0.1}))
                self.assertEqual(idle["status"], "idle")
                self.assertFalse((await asyncio.to_thread(http, runtime, "GET", "/status"))["waiting"])
        self.assertFalse((runtime_dir / "instances" / (state["instance_id"] + ".json")).exists())


if __name__ == "__main__":
    unittest.main()
