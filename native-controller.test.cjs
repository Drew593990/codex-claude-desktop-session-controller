const test = require('node:test');
const assert = require('node:assert/strict');
const { visibleRecordEvents } = require('./native-controller.cjs');

test('transcript reader excludes API snapshots, hidden reasoning, and injected system reminders', () => {
  const records = [
    { type: 'api-request', message: { role: 'user', content: 'INTERNAL_REQUEST_SNAPSHOT' } },
    { type: 'user', message: { role: 'user', content: '<system-reminder>INTERNAL_METADATA</system-reminder>' } },
    { type: 'user', uuid: 'request-1', message: { role: 'user', content: '用户可见任务' } },
    { type: 'assistant', uuid: 'answer-1', message: { role: 'assistant', content: [
      { type: 'thinking', thinking: 'PRIVATE_REASONING' },
      { type: 'text', text: '用户可见结果' },
      { type: 'tool_use', name: 'native_test_tool', input: { secret: 'TOOL_PAYLOAD' } },
    ] } },
  ];
  const events = records.flatMap(visibleRecordEvents);
  assert.deepEqual(events.map(e => e.text || e.name), ['用户可见任务', '用户可见结果', 'native_test_tool']);
  assert.equal(JSON.stringify(events).includes('PRIVATE_REASONING'), false);
  assert.equal(JSON.stringify(events).includes('TOOL_PAYLOAD'), false);
});
