# Codex–Claude Desktop Session Controller

[English](README.md) · [完整操作流程](docs/USAGE.md) · [相似项目对比](docs/COMPARISON.md) · [隐私与数据](SECURITY.md) · [验证范围](docs/VALIDATION.md)

让 Codex 通过本机原生消息，与 **Claude Desktop 的 Code 会话**协作。默认新建独立工作会话；用户指定旧会话时，可以跨项目接续原会话。任务、过程和结果留在原桌面对话中，用户可以查看、插话、中断并接管。

核心流程是 **Codex → 已有 Claude 桌面控制会话 → 桌面原生会话管理工具 → 工作会话**。创建、读取和停止由桌面内的控制会话调用实际工具完成；活跃工作会话也可直接通过原生 peer 管道收发。

## 适用条件

- Windows 本机，已能使用 Codex 和 Claude Desktop Code。
- Python 3.11+、Node.js 22+；运行桥接 MCP 的 Python 已安装 `mcp==1.26.0`。
- Claude 桌面的登录和模型推理已经可用，控制器已启用本项目 MCP。

桥接不调用外部模型 API，不额外索取模型 API Key，也不解密 Claude 官方账号 OAuth 缓存。但这**不等于无需登录官方账号也一定可用**：桌面端必须已有可工作的认证/推理配置。第三方网关只验证过原型所在的一套现有配置，不承诺所有网关都兼容。

普通 Chat、Cowork、WSL、macOS、自动启动应用及自动登录均不在已验证范围。

## 安装

以下是虚构示例路径，换成自己的永久位置。源码目录与控制器工作目录应分开：

```powershell
git clone https://github.com/Drew593990/codex-claude-desktop-session-controller.git
Set-Location codex-claude-desktop-session-controller
python -m pip install -r requirements.txt
python scripts/install.py --workspace 'D:\Projects\claude-desktop-native-bridge' --register
```

没有把 Python、Node 加入 PATH 时，使用其可执行文件绝对路径；Node 可通过 `--node` 指定，控制器 Python 可通过 `--python` 指定。安装器自身不会执行 pip、启动模型或发送任务。

安装器会复制必要运行文件、合并项目 `.mcp.json`，并把本机路径填入生成的 skill。只有加上 `--register`，才会备份并更新 Codex 全局配置和规则；不加则只安装技能和工作区文件。它不会修改 Claude 账号、模型、权限或入站策略，不会覆盖不认识或被用户改过的文件。

## 首次启用

1. 在 Claude Desktop 的 **Code** 标签页打开刚选定的桥接工作目录。
2. 按 Claude 正常提示启用项目 `codex_bridge` MCP。允许接入不等于批准任意后续任务。
3. 在这个桌面对话中发送：

   > 开启本项目的 Codex 收件，按 CLAUDE.md 执行。先报告 bridge_status，再调用 wait_for_task。收到任务和结果时在桌面对话展示；我接管或要求停止时就停止等待。

4. 在 Codex 刷新技能列表；若当前聊天未刷新，另开一个 Codex 聊天再使用。也可通过全局规则的准确路径读取入口。
5. 检查 `client.py status`，确认控制器实例 `waiting=true`。有多个实例时必须匹配控制器，不能随便选一个。

这一步由用户正常授权。桥接不会自动代点、放宽权限或启用调试端口。

## 两种调用方式

**默认新建工作会话：**

> 使用 `$codex-claude-desktop-session-controller`，请 Claude 只读审查我提供的文件，列出问题及依据，不修改原文件。

Codex 定位控制器后，要求它在桥接项目下只创建一个 fresh 工作会话，不 fork、不建 worktree，沿用桌面默认模型、effort 和权限。取得会话 ID 后核对实际目录和回复。后续修订继续使用该工作会话。

**明确指定已有会话：**

> 接续 Claude 桌面中已有的“我的研究会话”，先读最近记录，再发送这次检查任务。不要新建会话，也不要改研究文件。

目标可以在其他项目目录。必须保留原 ID、原目录、原历史；不能因为不在桥接目录而拒绝，或偷偷创建同名替代。遇到重名应澄清；仅要求读取时不发消息。忙碌或等待用户审批时，不自行中断覆盖。

创建工具的“继承当前项目”参数约束只适用于**新建**，不能套用到读取或接续其他项目的已有会话。

## 人工查看和接管

用户在 Claude 原有桌面对话中查看任务与工具过程，可以直接补充要求，或点击停止后自己继续。Codex 会读取实际回复并核验；收到用户停止、暂停或接管指令后，不应自动重启工作。

这里没有统一三方面板，也没有实现任一方插话都自动同步另一方。Claude 返回结果通过既有任务协议或 Codex 读取；不要把它理解为完整的自主双向消息平台。

## 功能与限制

- 原型已实测：原生唤醒、创建桌面工作会话、收发与读取、停止测试回合、跨项目接续旧会话、Codex 子智能体执行同样的受限流程。
- 本次发布新增的可移植安装器验证了临时目录配置生成和保留用户文件；尚未用它替换原型的现场环境做全新安装后的桌面验收。
- 控制器仍要可连接；冷启动、账号登录、自动分屏和普通 Chat 不在实现范围。
- MCP 任务队列在内存中，进程退出后不会自动恢复；日志不等于可重放队列。
- 管道写入成功不等于模型已读，出现一句回复不等于研究工作已完成。
- 本机原生接口依赖应用版本；模型名称、权限类别和会话 ID 都不能写死。

更详细的操作、停止、排错、更新与卸载见 [USAGE](docs/USAGE.md)。与 Triangle Bridge、KeeVeeG Desktop Bridge、AgentBridge 和 CCB 的区别见 [COMPARISON](docs/COMPARISON.md)。我们不主张“首个”“唯一”或全面强于它们。

## 隐私

公开仓库不包含开发者的个人目录、账号令牌、API Key、会话历史、运行日志、真实会话 ID 或本机配置。安装时在使用者机器上生成的路径只保存在本机。运行中的任务正文和结果会写入本地审计日志，并会被所选模型的现有服务处理；“本机桥接”不等于推理内容绝不上云。请阅读 [SECURITY](SECURITY.md)。

MIT 许可证；独立项目，不代表 OpenAI 或 Anthropic。
