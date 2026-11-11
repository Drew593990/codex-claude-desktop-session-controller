// Claude Desktop Code control through its native peer inbox. No model API,
// hidden Claude process, keyboard/mouse events, debugger, or credential changes.
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');
const { randomUUID, randomBytes } = require('node:crypto');

const home = path.join(process.env.USERPROFILE, '.claude');

function liveDesktopSessions() {
  const directory = path.join(home, 'sessions');
  const result = [];
  if (!fs.existsSync(directory)) return result;
  for (const filename of fs.readdirSync(directory)) {
    if (!/^\d+\.json$/.test(filename)) continue;
    try {
      const record = JSON.parse(fs.readFileSync(path.join(directory, filename), 'utf8'));
      if (!record.entrypoint?.startsWith('claude-desktop') || !record.hostSessionId?.startsWith('local_')) continue;
      process.kill(record.pid, 0); // Existence check only; does not send a stop signal.
      result.push(record);
    } catch { /* Ignore stale/unreadable registry entries, never modify them. */ }
  }
  return result;
}

function pickSession(id) {
  const matches = liveDesktopSessions().filter(s => s.sessionId === id || s.hostSessionId === id);
  if (matches.length !== 1) throw new Error('Select one exact live desktop session ID; ambiguous or stopped sessions are not guessed');
  return matches[0];
}

function readableSession(id) {
  const live = liveDesktopSessions().filter(s => s.sessionId === id || s.hostSessionId === id);
  if (live.length === 1) return live[0];
  if (live.length > 1) throw new Error('Ambiguous session ID');
  // Reading an exact historical transcript does not require a running engine.
  // Mutation/send operations still use pickSession and require a live desktop.
  if (/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i.test(id || '')) {
    return { sessionId: id, hostSessionId: null, status: 'not-running' };
  }
  throw new Error('For a stopped session supply its exact Claude UUID, or use the desktop-native session manager');
}

function peerCredential(target) {
  const directory = path.join(home, 'sessions');
  const start = String(target.procStartFt ?? target.procStart ?? '');
  const candidates = fs.readdirSync(directory)
    .filter(name => new RegExp(`^${target.pid}\\.[a-f0-9]{64}\\.key$`).test(name))
    .map(name => JSON.parse(fs.readFileSync(path.join(directory, name), 'utf8')))
    .filter(key => /^[a-f0-9]{32}$/.test(key.peerToken || '') &&
      start && String(key.procStartFt ?? key.procStart ?? '') === start &&
      (!target.pidDomain || key.pidDomain === target.pidDomain));
  if (candidates.length !== 1) throw new Error('A unique peer credential tied to the live process is required');
  return candidates[0].peerToken;
}

async function sendNative(target, text, permissionClass) {
  if (!['prompting', 'bypass'].includes(permissionClass)) throw new Error('Unknown sender permission class');
  if (!text.trim() || text.length > 100000) throw new Error('Message must contain 1-100000 characters');
  if (!/^\\\\\.\\pipe\\LOCAL\\cc-msg-[a-f0-9]{32}$/i.test(target.messagingSocketPath || '')) {
    throw new Error('Target is not a supported local Claude peer inbox');
  }
  const token = peerCredential(target); // Normal peer token, never the own-child token.
  const requestId = randomUUID();
  const senderPipe = '\\\\.\\pipe\\LOCAL\\cc-msg-' + randomBytes(16).toString('hex');
  const address = 'uds:' + senderPipe;
  // The actual sending agent must attest its REAL effective permission class.
  // Default is prompting. bypass is valid only when that agent truly runs tools
  // without approval; this must be checked in the sender's current runtime.
  // No user identity, permission approval, or existing Claude session is claimed.
  const body = `[Codex request ${requestId}]\n${text}`.replaceAll('</cross-session-message>', '&lt;/cross-session-message&gt;');
  const content = `<cross-session-message from="${address}" from-name="Codex Native Controller" from-mode="${permissionClass}">\n${body}\n</cross-session-message>`;
  const frame = { type: 'user', session_id: target.sessionId, uuid: requestId,
    msg_id: requestId, from: address, priority: 'next', message: { role: 'user', content } };
  return await new Promise((resolve, reject) => {
    const server = net.createServer(peer => peer.end());
    let socket, settled = false;
    const timer = setTimeout(() => finish(new Error('Native inbox write timed out')), 5000);
    function finish(error) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket?.destroy();
      server.close();
      if (error) reject(error);
      else resolve({ request_id: requestId, session_id: target.sessionId,
        host_session_id: target.hostSessionId, sender_permission_class: permissionClass,
        transport_written: true, delivery: 'not-yet-verified' });
    }
    server.on('error', finish);
    server.listen(senderPipe, () => {
      socket = net.connect(target.messagingSocketPath);
      socket.on('error', finish);
      socket.on('connect', () => socket.end(JSON.stringify({ type: 'auth', token }) + '\n' + JSON.stringify(frame) + '\n', () => finish()));
    });
  });
}

function readTranscript(target, since, limit) {
  const directory = path.join(home, 'projects');
  const files = fs.readdirSync(directory, { withFileTypes: true })
    .filter(entry => entry.isDirectory())
    .map(entry => path.join(directory, entry.name, target.sessionId + '.jsonl'))
    .filter(file => fs.existsSync(file));
  if (files.length !== 1) throw new Error('A unique transcript for the selected session was not found');
  const entries = [];
  let matched = !since;
  for (const line of fs.readFileSync(files[0], 'utf8').split('\n')) {
    let record;
    try { record = JSON.parse(line); } catch { continue; }
    if (!matched && record.uuid === since) matched = true;
    if (matched) entries.push(...visibleRecordEvents(record));
  }
  return { session_id: target.sessionId, host_session_id: target.hostSessionId,
    status: target.status, since_found: matched, events: entries.slice(-limit) };
}

function visibleRecordEvents(record) {
  if (!['user', 'assistant'].includes(record.type)) return [];
  const message = record.message;
  if (!message || !['user', 'assistant'].includes(message.role)) return [];
  const blocks = typeof message.content === 'string' ? [{ type: 'text', text: message.content }] : message.content;
  const result = [];
  for (const block of Array.isArray(blocks) ? blocks : []) {
    if (message.role === 'user' && block.type === 'text' && block.text.trimStart().startsWith('<system-reminder>')) continue;
    if (block.type === 'text') result.push({ role: message.role, timestamp: record.timestamp, uuid: record.uuid, text: block.text });
    else if (block.type === 'tool_use') result.push({ role: 'tool_call', timestamp: record.timestamp, name: block.name });
  }
  return result;
}

async function main() {
  const [action, ...rest] = process.argv.slice(2);
  const options = {};
  for (let index = 0; index < rest.length; index += 2) {
    if (!rest[index].startsWith('--') || rest[index + 1] === undefined) throw new Error('Options need explicit values');
    options[rest[index].slice(2)] = rest[index + 1];
  }
  let output;
  if (action === 'list') output = { sessions: liveDesktopSessions().map(s => ({ session_id: s.sessionId,
    host_session_id: s.hostSessionId, pid: s.pid, name: s.name, cwd: s.cwd, status: s.status })) };
  else {
    const target = action === 'read' ? readableSession(options.session) : pickSession(options.session);
    if (action === 'send') {
      if (!options.file) throw new Error('--file is required');
      output = await sendNative(target, fs.readFileSync(path.resolve(options.file), 'utf8'), options['sender-mode'] || 'prompting');
    } else if (action === 'read') {
      const limit = Number(options.limit || 20);
      if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new Error('Limit must be 1-100');
      output = readTranscript(target, options.since, limit);
    } else throw new Error('Use list, send --session ID --file PATH, or read --session ID [--since REQUEST_ID]');
  }
  console.log(JSON.stringify(output, null, 2));
}

if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode = 1; });
module.exports = { liveDesktopSessions, pickSession, readableSession, sendNative, readTranscript, visibleRecordEvents };
