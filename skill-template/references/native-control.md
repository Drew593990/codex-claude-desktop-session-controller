# Installed native control commands

Run PowerShell in the workspace:

```powershell
Set-Location -LiteralPath @@WORKSPACE_PS@@
& @@NODE_PS@@ native-controller.cjs list
& @@PYTHON_PS@@ -B -X utf8 client.py status
```

Match the controller by its project, receiving role and native PID against the inbox parent_pid. Do not guess among multiple sessions. `list` returns live Desktop Code engines, not every historical chat. It does not filter by workspace, so existing sessions in other projects remain addressable.

If the exact controller inbox is waiting:

```powershell
& @@PYTHON_PS@@ -B -X utf8 client.py send --instance '<instance-id>' --file '<task-file>'
& @@PYTHON_PS@@ -B -X utf8 client.py result --instance '<same-instance-id>' --task-id '<task-id>'
```

Tell the controller to display the task/result and submit_result, then continue waiting only while receiving remains enabled. The queue is in-memory; a process restart does not replay or recover tasks automatically. Read history and reconcile before sending again.

For a live exact session that is idle without a waiting MCP call:

```powershell
& @@NODE_PS@@ native-controller.cjs send --session '<exact-host-id-or-sdk-uuid>' --file '<task-file>' --sender-mode prompting
& @@NODE_PS@@ native-controller.cjs read --session '<same-id>' --since '<request-id>' --limit 20
```

Declare actual sender permission class. Default prompting; use bypass only if this sending agent actually runs tools without approval. It is not a retry trick or a grant to the receiver. Never use an own-child token or impersonate another session. A real peer token is read locally and never belongs in a prompt or report.

The send result only confirms transport_written; read the actual request and assistant reply. `read --since` matches a transcript UUID, including this client's request_id. Desktop SendMessage's message_id may differ; inspect a few recent visible entries and an agreed marker instead. The reader returns visible user/assistant text and tool names, not reasoning blocks, API snapshots or tool arguments. It is not a full paginated history browser.

Desktop tools are called by the Claude controller, not directly exposed to Codex: discover the current equivalents of start_session, list_sessions, get_session, list_events, SendMessage/send_message and stop_session. Names and schemas can change. Verify actual metadata and results. For default new work inherit this controller's current bridge project and omit cwd/target/host/environment/preset; do not apply that creation rule to other-project existing sessions.

An exact SDK UUID can read a unique saved transcript without a live engine. Sending requires a live engine; inactive host IDs need the Desktop manager to locate/continue the same session. No cold-start or login automation is promised. No crossSessionInbound=accept setting is required by the installer; explicit receiver policy must be respected.
