# Validation and limits / 验证与边界

## Historical live checks

The original Windows prototype was exercised on 2026-11-11 with Claude Desktop 5.1231.2.0 and its Desktop-owned Code engine 2.1.321. App version labels identify the observed setup, not an assurance of support for all installations or providers.

Observed operations:

- Waking an idle controller with an ordinary authenticated local peer message, visible in its Desktop conversation.
- Creating one fresh Desktop Code work session through the controller's native start_session tool and reading its exact assistant reply.
- Sending a second message to that same session and reading its exact reply.
- Stopping a dedicated test session's waiting turn through Desktop stop_session while preserving the session.
- Reading an explicitly chosen old research session in another project and receiving its test reply without creating/forking a replacement.
- Repeating restricted create/continue and cross-project tests through Codex subagents, with parent verification of actual transcript entries.

No live usernames, account settings, project paths, session IDs or raw transcripts are published. These manual observations are historical evidence; the public repository tests cannot reconstruct them without the applications and normal user authorization.

## Public package validation

The runtime derives from the tested prototype. The portable installer and generated instructions are new packaging work. Temporary fixtures verify generated local paths, config parsing, Unicode/quoted folders, idempotency, conflict refusal and preservation of unrelated rules. The real MCP SDK integration test exercises stdio negotiation, loopback authentication, task claim/result, cancellation and timeout, with no model. The Node regression test checks which saved record types are exposed.

These checks do **not** establish a fresh-install end-to-end Desktop run, a provider/account compatibility matrix, or robustness under every concurrent workload. No claim that the installer automatically activates a running chat is made. A visible skill is not proof its MCP server connected.

## Known limitations

- Windows default-profile Desktop Code runtime registry only. Alternate CLAUDE_CONFIG_DIR profiles, WSL, remote hosts, macOS, Linux, hosted Chat and Cowork are not validated by this release.
- The controller must be reachable. No automatic cold start, login, global setting repair or permission approval.
- Default new-session creation inherits the controller's project; arbitrary-folder creation remains subject to Desktop restrictions. Existing sessions may belong to other projects.
- Current MCP queue/task map are in-memory. Audit files are not replayed after restart.
- Native sender does not implement a durable outbox, automatic deduplication or full parent-chain receipt algorithm. Never blindly repeat uncertain sends.
- The read helper loads a transcript file and returns a limited tail. It is not an incremental/paginated large-history API. Concurrent user messages require additional marker/state checks.
- MCP completed is a collaborator report; verify the actual reply and research artifacts.
- User takeover remains in the original app. No unified panel, automatic mirroring of all human inputs or independent Claude-to-Codex wakeup service.
- Split-screen APIs refused in the prototype and are not required or implemented here.
- Desktop tool names and local registry/pipe formats may change. No app patching or hidden CLI fallback is supplied.

## 中文说明

原型现场验证、可移植安装测试、协议测试、静态检查是不同证据。发布时保留这些边界，不把“代码存在”“配置可解析”“别人报告通过”写成当前桌面功能已成功运行。遇到未知版本或配置，请先做只读发现，再在正常授权下使用专用测试会话验证；不要拿真实研究任务做破坏性兼容测试。
