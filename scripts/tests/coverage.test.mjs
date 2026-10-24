import assert from 'node:assert/strict';
import childProcess from 'node:child_process';
import { readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import { join } from 'node:path';
import test from 'node:test';
import { MATRIX, ROOT, coverageCheckout, implementation, json, rejects, sha256, writeJSON } from './support.mjs';

const checker = () => implementation('check-coverage', 'checkCoverage');

test('accountability enumerates exactly CORE-001..028 with bounded per-role assessments and explicit gaps', async () => {
  const { checkCoverage } = await checker();
  const result = checkCoverage();
  assert.equal(result.status, 'coverage_integrity_checked');
  assert.equal(result.requirements, 28);
  assert.ok(result.localAnchorsChecked > 0);
  assert.ok(result.externalAnchorsUnchecked > 0);
  assert.equal(result.testsExecuted, 0);
  assert.equal(result.fullCoreConformance, false);
  assert.equal(result.externallyIndependentEvaluations, 0);
  const matrix = json(ROOT, MATRIX);
  assert.deepEqual(matrix.requirements.map(row => row.id),
    Array.from({ length: 28 }, (_, i) => `CORE-${String(i + 1).padStart(3, '0')}`));
});

for (const [label, mutate] of [
  ['missing requirement', m => { m.requirements.pop(); }],
  ['duplicated requirement', m => { m.requirements[27] = m.requirements[0]; }],
  ['invented requirement', m => { m.requirements[27].id = 'CORE-029'; }],
  ['missing role assessment', m => { delete m.requirements[0].implementations.javascript_refund.roleSupport.consumer; }],
  ['unknown role', m => { m.requirements[0].accountableRoles.push('certifier'); }],
  ['unbounded support label', m => { m.requirements[0].implementations.javascript_refund.roleSupport.consumer = 'supported'; }],
  ['missing positive anchor', m => { m.requirements[0].implementations.javascript_refund.positive = []; }],
  ['missing negative anchor', m => { m.requirements[0].implementations.javascript_refund.negative = []; }],
  ['hidden untested obligations', m => { m.requirements[0].implementations.javascript_refund.untested = []; }],
  ['unknown evidence identifier', m => { m.requirements[0].implementations.javascript_refund.positive = ['imagined-test']; }],
  ['array-valued file identifier', m => {
    m.anchors['js-accept'].file = ['js-tests'];
    m.anchors['js-accept'].selector = "test('nonexistent test', () => {";
  }],
  ['number-valued file identifier', m => {
    m.files['0'] = m.files['js-tests'];
    m.anchors['js-accept'].file = 0;
    m.anchors['js-accept'].selector = "test('nonexistent test', () => {";
  }],
  ['implementation mislabeled as test', m => { m.requirements[0].implementations.javascript_refund.positive = ['js-check']; }],
  ['claim promotion', m => { m.claims.fullCoreConformance = true; }],
  ['invented external evaluation', m => { m.claims.externallyIndependentEvaluations = 1; }],
  ['authority promotion', m => { m.implementations.python_refund.authority = 'granted'; }],
  ['hidden unsupported authority capability', m => { m.implementations.javascript_refund.unsupportedCapabilities = []; }],
  ['external evidence presented as local', m => { m.repositories.bench.verification = 'local_file_integrity_only'; }],
  ['mutable external revision', m => { m.repositories.bench.revision = 'main'; }],
  ['unknown matrix key', m => { m.allow = true; }],
  ['unknown assessment key', m => { m.requirements[0].implementations.javascript_refund.passed = true; }],
  ['missing normative source', m => { m.requirements[0].normativeAnchor = '**CORE-099:**'; }],
]) {
  test(`accountability rejects ${label}`, async t => {
    const { checkCoverage } = await checker();
    const root = coverageCheckout(t);
    const matrix = json(root, MATRIX);
    mutate(matrix);
    writeJSON(root, MATRIX, matrix);
    rejects(() => checkCoverage({ root }), 'invalid_coverage');
  });
}

test('accountability fails on missing or changed local source rather than crediting a link', async t => {
  const { checkCoverage } = await checker();
  for (const remove of [false, true]) {
    const root = coverageCheckout(t);
    const file = join(root, json(root, MATRIX).files['js-consumer'].path);
    if (remove) rmSync(file);
    else writeFileSync(file, Buffer.concat([readFileSync(file), Buffer.from('\n')]));
    rejects(() => checkCoverage({ root }), remove ? 'missing_path' : 'source_digest_mismatch');
  }
});

test('accountability fails on stale local test anchors even when the path exists', async t => {
  const { checkCoverage } = await checker();
  const root = coverageCheckout(t);
  const matrix = json(root, MATRIX);
  matrix.anchors['js-accept'].selector = "test('nonexistent test', () => {";
  writeJSON(root, MATRIX, matrix);
  rejects(() => checkCoverage({ root }), 'anchor_mismatch');
});

test('accountability distinguishes pinned external citation shape from external file verification', async t => {
  const { checkCoverage } = await checker();
  const root = coverageCheckout(t);
  const matrix = json(root, MATRIX);
  for (const file of Object.values(matrix.files)) {
    if (file.repository === 'bench') file.path = 'runtime-pilot/absent-in-this-checkout.py';
  }
  writeJSON(root, MATRIX, matrix);
  const result = checkCoverage({ root });
  assert.ok(result.externalAnchorsUnchecked > 0);
  assert.equal(result.testsExecuted, 0);
});

test('integrity checks do not run cited tests, import consumers, fetch URLs, or invoke Bench', async t => {
  const { checkCoverage } = await checker();
  const { verifyCandidate } = await implementation('verify-candidate', 'verifyCandidate');
  const root = coverageCheckout(t);
  const matrix = json(root, MATRIX);
  const file = matrix.files['js-tests'];
  const bytes = Buffer.concat([readFileSync(join(root, file.path)), Buffer.from('\nthrow new Error("must not execute");\n')]);
  writeFileSync(join(root, file.path), bytes);
  file.sha256 = sha256(bytes);
  writeJSON(root, MATRIX, matrix);
  const forbidden = () => assert.fail('Integrity checking must not use network, child processes, or cited tests');
  t.mock.method(globalThis, 'fetch', forbidden);
  t.mock.method(net.Socket.prototype, 'connect', forbidden);
  for (const object of [http, https]) {
    t.mock.method(object, 'request', forbidden);
    t.mock.method(object, 'get', forbidden);
  }
  for (const method of ['spawn', 'spawnSync', 'exec', 'execSync', 'execFile', 'execFileSync', 'fork']) {
    t.mock.method(childProcess, method, forbidden);
  }
  assert.equal(checkCoverage({ root }).testsExecuted, 0);
  assert.equal(verifyCandidate().testsExecuted, 0);
});

test('accountability rejects symlinks and escaping local paths', async t => {
  const { checkCoverage } = await checker();
  const root = coverageCheckout(t);
  const matrix = json(root, MATRIX);
  const file = matrix.files['js-consumer'];
  rmSync(join(root, file.path));
  symlinkSync(join(ROOT, file.path), join(root, file.path));
  rejects(() => checkCoverage({ root }), 'symlink_path');
  file.path = '../outside.mjs';
  writeJSON(root, MATRIX, matrix);
  rejects(() => checkCoverage({ root }), 'unsafe_path');
});

test('accountability rejects duplicate JSON members, invalid encodings, and over-limit input', async t => {
  const { checkCoverage } = await checker();
  for (const [raw, reason] of [[Buffer.from('{"format":1,"format":1}'), 'invalid_coverage'],
    [Buffer.from([0xff]), 'invalid_coverage'], [Buffer.alloc(512 * 1024 + 1, 32), 'limit_exceeded']]) {
    const root = coverageCheckout(t);
    writeFileSync(join(root, MATRIX), raw);
    rejects(() => checkCoverage({ root }), reason);
  }
});

test('accountability CLI reports integrity only and nonzero failure separately from consumer outcomes', async t => {
  await checker();
  const root = coverageCheckout(t);
  const cli = join(ROOT, 'scripts/check-coverage.mjs');
  const run = args => childProcess.spawnSync(process.execPath, [cli, ...args], {
    cwd: root, encoding: 'utf8', timeout: 10000,
  });
  const valid = run(['--root', root]);
  assert.equal(valid.status, 0, valid.stderr);
  assert.equal(valid.stderr, '');
  assert.equal(JSON.parse(valid.stdout).testsExecuted, 0);
  rmSync(join(root, MATRIX));
  const missing = run(['--root', root]);
  assert.equal(missing.status, 2);
  assert.equal(missing.stdout, '');
  assert.equal(JSON.parse(missing.stderr).reason, 'missing_path');
  const argumentsError = run(['--fetch', 'synthetic-private-marker']);
  assert.equal(argumentsError.status, 2);
  assert.equal(JSON.parse(argumentsError.stderr).reason, 'invalid_arguments');
  assert.ok(!argumentsError.stderr.includes('synthetic-private-marker'));
});
