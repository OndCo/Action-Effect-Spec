import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, symlinkSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

test('unexpected handler failure stays an evaluation failure and never echoes its error text', async () => {
  const { handleFrame } = await import('./cli.mjs');
  assert.equal(typeof handleFrame, 'function');
  const input = Buffer.from(JSON.stringify({ id: 'fault', op: 'check', document_b64: 'e30=' }));
  const actual = handleFrame(input, () => { throw new Error('private error detail'); });
  assert.deepEqual(actual, { id: 'fault', result: {
    status: 'evaluation_failure', reason: 'internal_error', authority: 'not_evaluated'
  } });
});

const cli = fileURLToPath(new URL('./cli.mjs', import.meta.url));
const hello = Buffer.from(JSON.stringify({ id: 'hello', op: 'hello' }));
const execute = (input, args = []) => spawnSync(process.execPath, [cli, ...args], {
  input, cwd: '/tmp', encoding: 'utf8', timeout: 10000, maxBuffer: 4 * 1024 * 1024
});
const output = result => result.stdout.trim().split('\n').filter(Boolean).map(JSON.parse);

test('CLI works from another cwd and recovers after a malformed frame', () => {
  const document = readFileSync(new URL('../../examples/partial-refund.json', import.meta.url));
  const request = JSON.stringify({ id: 'check', op: 'check', document_b64: document.toString('base64') });
  const result = execute(Buffer.concat([hello, Buffer.from('\nnot-json\n' + request + '\n')]));
  assert.equal(result.status, 0, result.stderr);
  const rows = output(result);
  assert.equal(rows.length, 3);
  assert.equal(rows[0].result.status, 'capabilities');
  assert.equal(rows[1].id, null);
  assert.equal(rows[1].result.reason, 'transport');
  assert.equal(rows[2].result.status, 'accepted_partial');
});

test('invalid/noncanonical base64 cannot be silently repaired', () => {
  const input = ['e30', 'e31=', 'e3 0=', '%%%%'].map(value => JSON.stringify({
    id: 'invalid', op: 'check', document_b64: value
  })).join('\n');
  const result = execute(Buffer.from(input));
  assert.equal(result.status, 0, result.stderr);
  assert.equal(output(result).length, 4);
  assert.ok(output(result).every(row => row.id === null && row.result.reason === 'transport'));
});

test('oversized frame is drained and next request is still processed', () => {
  const result = execute(Buffer.concat([Buffer.alloc(2 * 1024 * 1024 + 1, 32), Buffer.from('\n'), hello]));
  assert.equal(result.status, 0, result.stderr);
  const rows = output(result);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].result.reason, 'limit_exceeded');
  assert.equal(rows[1].result.status, 'capabilities');
});

test('document byte cap is distinct from adapter framing', () => {
  const result = execute(Buffer.from(JSON.stringify({ id: 'large', op: 'check',
    document_b64: Buffer.alloc(1024 * 1024 + 1, 32).toString('base64') })));
  assert.equal(result.status, 0, result.stderr);
  const [row] = output(result);
  assert.equal(row.id, 'large');
  assert.equal(row.result.status, 'evaluation_failure');
  assert.equal(row.result.reason, 'limit_exceeded');
});

test('bad startup configuration exits nonzero, not a semantic rejection', () => {
  const result = execute(hello, ['--basis', '/definitely-not-an-existing-basis.json']);
  assert.notEqual(result.status, 0);
  assert.equal(result.stdout, '');
  assert.match(result.stderr, /Unable to initialize offline consumer/);
});

test('blank frames and extra request fields rejected; final frame needs no newline', () => {
  const extra = JSON.stringify({ id: 'bad', op: 'hello', profile: 'untrusted' });
  const result = execute(Buffer.concat([Buffer.from('\n' + extra + '\n'), hello]));
  assert.equal(result.status, 0, result.stderr);
  const rows = output(result);
  assert.equal(rows.length, 3);
  assert.ok(rows.slice(0, 2).every(row => row.result.reason === 'transport'));
  assert.equal(rows[2].result.status, 'capabilities');
});

test('CLI invoked through a symlink actually produces a response', () => {
  const directory = mkdtempSync(join(tmpdir(), 'effect-cli-link-'));
  try {
    const alias = join(directory, 'consumer.mjs');
    symlinkSync(cli, alias);
    const result = spawnSync(process.execPath, [alias], {
      input: hello, cwd: directory, encoding: 'utf8', timeout: 10000,
    });
    assert.equal(result.status, 0, result.stderr);
    const rows = output(result);
    assert.equal(rows.length, 1, 'A successful exit without a result is not a completed check');
    assert.equal(rows[0].result.status, 'capabilities');
    assert.equal(rows[0].result.authority, 'not_evaluated');
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('CLI remains import-safe from a stdin module with no file entry point', () => {
  const url = new URL('./cli.mjs', import.meta.url).href;
  const result = spawnSync(process.execPath, ['--input-type=module', '-'], {
    input: `await import(${JSON.stringify(url)}); console.log('import-only');`,
    cwd: tmpdir(), encoding: 'utf8', timeout: 10000,
  });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, 'import-only\n');
});
