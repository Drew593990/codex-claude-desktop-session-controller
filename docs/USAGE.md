# 操作手册 / Operational guide

## 安装前检查

选择一个专用、可写的桥接目录。不要指向研究项目、磁盘根或源码 checkout 本身。确认桌面 Code 已能正常回答，Python 可导入 MCP，Node 可运行。安装依赖前先使用现有环境；项目不要求新建虚拟环境。

`scripts/install.py --workspace <absolute-path>` 安装工作文件和 skill；`--register` 额外备份并登记 Codex config 与全局规则。`--codex-home` 可指定非默认 Codex 目录。`--python` 是实际运行 MCP 的解释器，必须自己安装依赖；`--node` 可指定 Node 可执行文件。

安装器只打印本机安装位置与变更数量，不捕获环境中的 API Key。不要把生成文件和备份复制到公开仓库。

## 控制器与工作会话

控制器是用户在桥接项目里打开并启用收件的现有 Claude 桌面 Code 对话；工作会话是它通过桌面工具创建或按用户指定接续的目标。两者 ID 不同。控制器原生管理工具不是直接注册给 Codex 的工具，Codex 是通过消息让 Claude 在其桌面会话内调用它们。

控制器只在用户启用后等待。可使用启动语：

> 开启本项目的 Codex 收件，按 CLAUDE.md 执行，先报告 bridge_status，然后 wait_for_task，直到我接管或停止。

必须保留其正常权限确认；peer 消息不能充当用户批准。模型选择、账号和其他项目规则保持原样。

## 连接发现

在生成的桥接目录中运行（替换 python/node 为实际可执行文件）：

```powershell
node native-controller.cjs list
python -B -X utf8 client.py status
```

第一条只列活跃 Desktop Code 引擎。第二条会列出本工作区可连接的 MCP 实例。用项目、标题、收件角色和 native PID 对应 status 的 parent_pid，定位控制器。`waiting=true`、`current_task=null` 才说明该实例正在等新任务。

旧会话没有活跃引擎时，要求控制器调用桌面 list_sessions/get_session 定位原 ID；不能把 native list 没列出解释为其他项目不可接管。

## 任务收发

把任务写入 UTF-8 文本文件。正文应包含目标、新建/已有模式、原文件路径、输出位置、允许修改范围以及验收依据。

```powershell
python -B -X utf8 client.py send --instance '<exact-instance-id>' --file '.\task.txt'
python -B -X utf8 client.py result --instance '<same-instance-id>' --task-id '<returned-task-id>'
```

状态 queued/claimed/completed/blocked/failed 表达这项任务的流程；completed 是接收方提交的结果，需要核对原始回复/产物，不能当作可信证明。任务队列仅在进程内，重启先检查目标实际历史，避免重复执行。

对空闲但未调用 wait_for_task 的活跃会话，可以发送原生 peer 消息：

```powershell
node native-controller.cjs send --session '<exact-host-id-or-sdk-uuid>' --file '.\task.txt' --sender-mode prompting
node native-controller.cjs read --session '<same-id>' --since '<request-id>' --limit 20
```

sender-mode 必须如实反映发送方权限：默认 prompting，仅在当前 agent 确实无需工具审批时用 bypass。不能在被拒后冒报模式重试。接收端仍可 hold/refuse；不得修改入站策略来强行送达。

直接原生消息没有 MCP task_id，因此直接读取回复，不让控制器把不存在的任务 ID 交给 submit_result。脚本返回 transport_written 只说明管道写入。`read --since` 按记录 UUID 筛选，不是完整的父子消息关联算法；复杂交错回合需核对独特标记、实际记录和状态。

## 新建规则

默认在桥接目录新建 fresh 会话。先核对控制器 cwd，再继承当前项目：省略 cwd/target/host/environment/preset，不 fork、不建 worktree，不指定模型、effort 和权限。已实测显式重复 cwd 可能被应用判成异地创建；仅当工具明确 Not started 且目标确为当前目录时，才按其提示省略冗余参数。不要把这一参数修正当作规避其他拒绝的办法。

如果创建结果不明，先查实际会话，不盲目重试。明确指定其他新建目录但工具不允许时，应报告实际限制，不能默默落到桥接目录。

## 已有会话、停止与人工接管

用户按标题或准确 ID 指定已有会话后，核对原目录和状态，读取必要的最近历史。原目录可以是其他研究项目；继续原 ID，遵守其项目规则。若仅授权读取，就不发送。用户明确要求停止时，让控制器调用当前 stop_session 等效工具，确认目标回合停止且会话保留；不要停止控制器或其他工作。

用户可在 Claude 原窗口停止和继续。Codex 不应自动恢复用户中断的工作，也不在完成后自动删除、归档或清空会话。控制器恢复收件只在用户仍希望开启时进行。

## 排错

| 情况 | 检查与动作 |
| --- | --- |
| skill 可见但 Claude MCP 不可用 | 在 Claude Code 确认项目服务器是否启用，检查其启动错误；skill 可见不等于连接成功 |
| Python 提示找不到 mcp | 为 `.mcp.json` command 指向的解释器安装 requirements；不要误装到另一套 Python |
| client 显示不在 waiting | 确认用户是否接管了控制器；在用户授权下恢复收件，或对已核实的活跃控制器发原生消息 |
| 多个实例/重名会话 | 核对 PID、父 PID、目录和准确 ID，不猜测 |
| 管道写入后没有回复 | 检查接收端状态与入站提示，读取原会话；不要自动重发或放宽权限 |
| 窗口接口拒绝分屏 | 本流程不依赖分屏，手动打开目标对话即可 |
| 应用关闭、控制器不可达 | 本版无已验证的自动冷启动路径，让用户打开桥接项目并启用收件 |
| 升级后原生结构变化 | 记录应用版本和非敏感错误，报告未完成；不改缓存或安装另一套隐藏 CLI 代替 |
| 安装器拒绝覆盖 | 检查已有文件的用户修改和备份；不要删除文件来规避保护，可选择新的空工作区 |

## 更新与卸载

先保留运行中的旧环境。拉取源码后在方便时重新安装；安装器只更新未被用户改动的已管理文件。需要加载新 MCP 时由用户在桌面停止旧控制器并按应用正常方式重新加载。不要自动重启正在工作的应用。

卸载时先停用控制器：在 Codex 删除或禁用准确的 skill 注册，移除 AGENTS 中该 skill 的 begin/end 标记块，在项目 `.mcp.json` 仅移除 codex_bridge。按需删除安装器清单中属于本项目的文件。保留用户的其他服务器、配置、研究产物与会话；全局文件可从本地 `.backup-*` 恢复，但恢复前应检查后续用户改动。没有破坏性自动卸载脚本。

## English summary

Enable one controller in the dedicated workspace through normal Claude MCP authorization. Match native session PID to inbox parent_pid, then send a concrete task once. Default work creates a fresh Desktop Code session; explicit old-session requests preserve the exact ID across project folders. Read the target's actual response and inspect artifacts. Human interruption takes priority. All paths in generated skill/config files are local; do not publish those files or the `.bridge` runtime directory.
