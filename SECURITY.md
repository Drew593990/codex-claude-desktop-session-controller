# Local data and security / 本地数据与隐私

This is a same-user collaboration tool, not a security boundary between mutually untrusted agents. It uses local Windows application interfaces and the receiving application's actual permissions. Independent of OpenAI and Anthropic.

## Data handling

- Installation writes only the selected workspace, rendered skill, optional backed-up Codex registration/rule block, and local install manifest. It does not enumerate or export environment secrets.
- Native discovery reads same-user Claude session metadata. Ordinary peer keys are used in memory for local pipe authentication. They are not OAuth account tokens and are not printed or put into prompts. Own-child credentials are not used.
- The MCP inbox binds random-port **127.0.0.1**, validates Host, rejects browser Origin requests and requires its random bearer token. Its discovery file contains that token and must remain private under the user's local filesystem permissions. It is not a remotely hosted API.
- `.bridge/*-events.jsonl` records local task text and submitted answers. The task map and queue exist only in process memory; logs are not replayed.
- `read` reads a specifically addressed local conversation and exposes selected visible message text and tool names. It filters reasoning blocks, API snapshots and injected system reminders. It is not a content scrubber; user text may itself contain private information.
- Messages sent to a model are processed through that application's existing inference service and policy. A local bridge does not make cloud inference local or prevent the selected provider from processing supplied text.

Do not commit `.bridge`, runtime discovery files, local `.mcp.json`, generated instructions containing personal paths, API keys, tokens, real transcripts, backups or live session identifiers. Public source excludes those assets. Runtime permissions are those of the user's account; choose a private directory and protect local backups.

## Permission semantics

Native messages identify a collaborator, not a human typing. The sender must truthfully declare prompting or bypass according to its actual execution permissions. This is not a toggle for overcoming a refusal. Receiving hold/refuse rules and tool approvals still apply. Never modify permissions, account settings or application files to make a blocked action run elsewhere.

The controller uses Desktop session-management tools under its own rules. The bridge does not decrypt account OAuth caches, start model CLI jobs, open debuggers, patch app files, change the selected model, or automatically approve tool calls. Existing Desktop authentication must already work; no extra API key is requested. Login-free or official-account-free operation is not established by this claim.

## Reporting

Use GitHub's private vulnerability-reporting channel if enabled. If unavailable, open a minimal issue asking for a private reporting route without including exploit secrets or account data. Do not post transcripts, runtime keys, local configuration, account cache files or full process command lines. Prefer application versions, a redacted symptom and synthetic fixtures. Unknown delivery should be inspected rather than resent.

## 中文提示

公开源码不应含任何开发者本机信息。使用者运行后生成的路径、实例和日志仅在其本机；别把整个安装工作目录上传。任务正文与答案会写本地审计日志，并交给目标模型处理。移除某项本地日志前先确认用户不再需要它；本项目没有自动清理用户会话或研究文件的脚本。
