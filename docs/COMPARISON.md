# Similar projects / 相似项目对比

Reviewed on 2026-11-11. This is a source/documentation comparison, **not** a head-to-head installation benchmark. Features and interfaces change. Our live evidence is limited to the original Windows prototype; no claim of uniqueness or overall superiority is made. All projects retain their own authorship; no competitor implementation code is included here.

## Triangle Bridge

Source snapshot: [heelee912/triangle-bridge, c042c5e, package 0.3.2](https://github.com/heelee912/triangle-bridge/tree/c042c5e6ee5161fae99809b329afb95c9acabf5d).

It covers three desktop apps, exact-session operations, creation, native message delivery and local response reading. Its transport reconciliation, application startup and self-contained installation are broader than this project's current implementation. Cross-project addressing and native-history reading overlap and are not unique here. [README](https://github.com/heelee912/triangle-bridge/blob/c042c5e6ee5161fae99809b329afb95c9acabf5d/README.md).

| Area | Triangle Bridge | This project |
| --- | --- | --- |
| Scope | Codex, Claude Desktop Code, Antigravity | Codex-driven Claude Desktop Code tasks |
| Claude management | Scripts address Desktop and runtime interfaces | Existing visible Claude controller calls the Desktop tools exposed to it |
| Create | `code create` does a child CLI first turn then imports; `code start` also has renderer/raw direct-start paths | Controller calls the available native Desktop start_session tool |
| Account credentials | The create/import path reads Desktop OAuth cache; peer/live-stdin sends do not | No account OAuth cache extraction in the controller creation workflow; native peer credentials remain necessary |
| Defaults | Creation paths include permission/model choices; ordinary sends preserve recipient settings | Skill requests inherited model/effort/permissions, without overriding them |
| Task outcome | Delivery/request receipts and response selection | MCP claimed/completed/blocked/failed plus actual-result verification by Codex |
| Stop | No dedicated stop command found in the reviewed public Claude CLI switch | Prototype tested stopping a specified turn through the Desktop controller |
| Installation/recovery | Self-contained scripts, runtime discovery, app wake/start | Portable installer; controller must already be reachable; no cold-start automation |

The two creation paths must not be conflated. The CLI/import implementation can be inspected in [claude_session_create.mjs](https://github.com/heelee912/triangle-bridge/blob/c042c5e6ee5161fae99809b329afb95c9acabf5d/scripts/claude_session_create.mjs); direct-start handling also exists in [claude_code_bridge.mjs](https://github.com/heelee912/triangle-bridge/blob/c042c5e6ee5161fae99809b329afb95c9acabf5d/scripts/claude_code_bridge.mjs#L1511). Thus “only we can create Desktop sessions” is not a supported claim. Likewise, the project's account-cache dependence in one path does not mean all its operations require that token.

Our narrower path avoids controlling app-owned stdin handles and processing account OAuth tokens. It still depends on a local peer protocol and Desktop tools that can change. An intermediary controller adds model latency/use and a live-session dependency; it is not inherently faster or more robust. Native Desktop's own project and approval restrictions still apply.

Worth learning from: persistent send reservations, uncertain-delivery refusal, request/parent-chain reply correlation, incremental UTF-8 transcript tails, and synthetic/OS-pipe regression tests. These are not all implemented here; instructions to avoid duplicate sends are weaker than a durable deduplication system. See [peer transport](https://github.com/heelee912/triangle-bridge/blob/c042c5e6ee5161fae99809b329afb95c9acabf5d/scripts/claude_peer_transport.mjs) and [installation](https://github.com/heelee912/triangle-bridge/blob/c042c5e6ee5161fae99809b329afb95c9acabf5d/scripts/install_skills.mjs).

## KeeVeeG's Codex–Claude Desktop Bridge

Source snapshot: [d0e8416, v0.4.2](https://github.com/KeeVeeG/codex-claude-desktop-bridge/tree/d0e8416ad834df87dcf0c86a22dab1c1f8045b96).

It explicitly supports Desktop Code and other local Code entrypoints, asynchronous messages in both directions and an MCP Apps panel for manual human messages. We do not offer an equivalent unified panel or unsolicited full-duplex delivery into Codex. Its visible panel and bidirectional messaging must not be presented as our unique advantages. [README](https://github.com/KeeVeeG/codex-claude-desktop-bridge/blob/d0e8416ad834df87dcf0c86a22dab1c1f8045b96/README.md#conversation-panel).

In the reviewed tool registry, creation and stopping were not exposed as bridge tools. Its native-history catalog extracts safe metadata; panel history concerns bridge exchanges, rather than returning unrelated native chat bodies. Our task controller additionally orchestrates Desktop session creation/stopping and reads requested original conversation text. These are current scope differences, not proof that the other project cannot add them. [Tools](https://github.com/KeeVeeG/codex-claude-desktop-bridge/blob/d0e8416ad834df87dcf0c86a22dab1c1f8045b96/scripts/mcp.mjs#L60), [history catalog](https://github.com/KeeVeeG/codex-claude-desktop-bridge/blob/d0e8416ad834df87dcf0c86a22dab1c1f8045b96/lib/claude-history.mjs#L144).

## AgentBridge and CCB

- [raysonmeng/agent-bridge](https://github.com/raysonmeng/agent-bridge): persistent bidirectional Claude Code/Codex coordination using a channel and app-server architecture; its documented launch workflow mainly uses CLI agents. Human steering and cross-review are already part of its scope.
- [SeemSeam/claude_codex_bridge](https://github.com/SeemSeam/claude_codex_bridge): a broader visible multi-provider CLI workspace with human takeover, queues and remote/mobile features.

These overlap in the collaboration goal, but are not the same narrow Desktop-controller implementation. This project is useful for people who deliberately prefer the existing Claude Desktop Code UI and want explicit default-new versus selected-existing task routing. It should be evaluated on that workflow, not a claim that other projects cannot support a desktop or a human participant.

## 中文结论

本项目的价值是一个可理解、可复现的窄流程：沿用已有桌面认证，让 Claude 自己的会话工具负责新建/接续/停止，默认不改模型与权限，并把任务完成和消息写入分开核验。对方在覆盖面、安装与投递可靠性上有值得学习的实现。仅有“支持桌面”“跨项目”或“用户可接管”不能成为独有卖点。
