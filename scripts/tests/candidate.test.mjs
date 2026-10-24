import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, renameSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { COMPONENTS, MANIFEST, ROOT, candidateCheckout, implementation, json, rejects, sha256, writeJSON } from './support.mjs';

const verifier = () => implementation('verify-candidate', 'verifyCandidate');

test('candidate pins the four original normative files without becoming a wire profile or a badge', async t => {
  const { verifyCandidate, MANIFEST_SHA256 } = await verifier();
  const root = candidateCheckout(t);
  const manifest = json(root, MANIFEST);
  assert.deepEqual(manifest.components.map(item => item.path).sort(), [...COMPONENTS].sort());
  assert.equal(sha256(readFileSync(join(root, MANIFEST))), MANIFEST_SHA256);
  const result = verifyCandidate({ root });
  assert.deepEqual(result, {
    status: 'candidate_integrity_checked', candidateId: 'github-issue-comment-1-candidate.1',
    profileVersion: 'github-issue-comment/1', normativeComponentsChecked: 4,
    authority: 'not_evaluated', fullCoreConformance: false, stable: false,
    securityCertified: false, externallyIndependentEvaluations: 0, testsExecuted: 0,
  });
  assert.equal(json(root, 'profiles/github-issue-comment/profile.json').authority, 'not_evaluated');
});

for (const path of COMPONENTS) {
  test(`candidate rejects changed normative bytes: ${path}`, async t => {
    const { verifyCandidate } = await verifier();
    const root = candidateCheckout(t);
    writeFileSync(join(root, path), Buffer.concat([readFileSync(join(root, path)), Buffer.from('\n')]));
    rejects(() => verifyCandidate({ root }), 'component_digest_mismatch');
  });
  test(`candidate rejects missing normative file: ${path}`, async t => {
    const { verifyCandidate } = await verifier();
    const root = candidateCheckout(t);
    rmSync(join(root, path));
    rejects(() => verifyCandidate({ root }), 'missing_path');
  });
}

test('candidate rejects absent manifest, directories, and symlink roots', async t => {
  const { verifyCandidate } = await verifier();
  const root = candidateCheckout(t);
  rmSync(join(root, MANIFEST));
  rejects(() => verifyCandidate({ root }), 'missing_path');
  mkdirSync(join(root, MANIFEST));
  rejects(() => verifyCandidate({ root }), 'not_regular_file');
  const alias = join(root, 'alias');
  symlinkSync(root, alias);
  rejects(() => verifyCandidate({ root: alias }), 'symlink_path');
});

for (const outside of [false, true]) {
  test(`candidate refuses ${outside ? 'external' : 'in-tree'} symlinks in files and ancestors`, async t => {
    const { verifyCandidate } = await verifier();
    for (const path of ['SPEC.md', MANIFEST, 'schemas']) {
      const root = candidateCheckout(t);
      const target = outside ? join(ROOT, path) : join(root, 'saved');
      if (outside) rmSync(join(root, path), { recursive: true });
      else renameSync(join(root, path), target);
      symlinkSync(target, join(root, path));
      rejects(() => verifyCandidate({ root }), 'symlink_path');
    }
  });
}

for (const path of ['../SPEC.md', '/etc/passwd', 'schemas/../SPEC.md', './SPEC.md',
  'schemas//file', 'schemas\\file', 'https://example.invalid/SPEC.md', 'C:/SPEC.md', '%2e%2e/SPEC.md', '']) {
  test(`candidate rejects noncanonical or escaping component paths: ${JSON.stringify(path)}`, async t => {
    const { verifyCandidate } = await verifier();
    const root = candidateCheckout(t);
    const manifest = json(root, MANIFEST);
    manifest.components[0].path = path;
    writeJSON(root, MANIFEST, manifest);
    rejects(() => verifyCandidate({ root }), 'unsafe_path');
  });
}

test('candidate rejects unknown keys at every manifest object boundary', async t => {
  const { verifyCandidate } = await verifier();
  const selectors = [m => m, m => m.source, m => m.profile, m => m.profile.digest,
    m => m.claims, m => m.scope, m => m.compatibility, m => m.failureSemantics, m => m.components[0]];
  for (const select of selectors) {
    const root = candidateCheckout(t);
    const manifest = json(root, MANIFEST);
    select(manifest).unrecognized = true;
    writeJSON(root, MANIFEST, manifest);
    rejects(() => verifyCandidate({ root }), 'invalid_manifest');
  }
});

test('candidate does not reinterpret unsupported versions or identities', async t => {
  const { verifyCandidate } = await verifier();
  for (const version of [0, 2, '1', null]) {
    const root = candidateCheckout(t);
    const manifest = json(root, MANIFEST);
    manifest.manifestVersion = version;
    writeJSON(root, MANIFEST, manifest);
    rejects(() => verifyCandidate({ root }), 'unsupported_manifest_version');
  }
  for (const mutate of [m => { m.candidateId = 'github-issue-comment-1-candidate.2'; },
    m => { m.profile.version = 'github-issue-comment/2'; }, m => { m.profile.id += '/latest'; },
    m => { m.profile.coreSpec = '1.0'; }, m => { m.compatibility.replacesWireProfile = true; }]) {
    const root = candidateCheckout(t);
    const manifest = json(root, MANIFEST);
    mutate(manifest);
    writeJSON(root, MANIFEST, manifest);
    rejects(() => verifyCandidate({ root }), 'invalid_manifest');
  }
});

test('candidate refuses promoted authority, stability, certification, or independent evaluation claims', async t => {
  const { verifyCandidate } = await verifier();
  for (const [key, value] of [['authority', 'granted'], ['stable', true], ['securityCertified', true],
    ['fullCoreConformance', true], ['externallyIndependentEvaluations', 1]]) {
    const root = candidateCheckout(t);
    const manifest = json(root, MANIFEST);
    manifest.claims[key] = value;
    writeJSON(root, MANIFEST, manifest);
    rejects(() => verifyCandidate({ root }), 'invalid_manifest');
  }
});

test('candidate rejects missing, duplicated, extra, and circular hash components', async t => {
  const { verifyCandidate } = await verifier();
  for (const mutate of [m => { m.components.pop(); }, m => { m.components.push(m.components[0]); },
    m => { m.components[0].path = MANIFEST; }, m => { m.components[0].path = 'scripts/verify-candidate.mjs'; },
    m => { m.components[0].sha256 = 'A'.repeat(64); }, m => { m.components[0].sha256 = 'a'.repeat(64) + '\n'; }]) {
    const root = candidateCheckout(t);
    const manifest = json(root, MANIFEST);
    mutate(manifest);
    writeJSON(root, MANIFEST, manifest);
    rejects(() => verifyCandidate({ root }), 'invalid_manifest');
  }
});

test('candidate manifest bytes have a noncircular pin outside the normative component set', async t => {
  const { verifyCandidate } = await verifier();
  const root = candidateCheckout(t);
  writeFileSync(join(root, MANIFEST), Buffer.concat([readFileSync(join(root, MANIFEST)), Buffer.from('\n')]));
  rejects(() => verifyCandidate({ root }), 'manifest_digest_mismatch');
});

test('changing a component and its advertised hash cannot rewrite the same candidate', async t => {
  const { verifyCandidate } = await verifier();
  const root = candidateCheckout(t);
  const manifest = json(root, MANIFEST);
  writeFileSync(join(root, 'SPEC.md'), 'different semantics\n');
  manifest.components.find(item => item.path === 'SPEC.md').sha256 = sha256(Buffer.from('different semantics\n'));
  writeJSON(root, MANIFEST, manifest);
  rejects(() => verifyCandidate({ root }), 'manifest_digest_mismatch');
});

test('candidate parsing rejects duplicate keys, invalid UTF-8, BOM, nonobjects, and unsupported numbers', async t => {
  const { verifyCandidate } = await verifier();
  for (const raw of [Buffer.from('{"manifestVersion":1,"manifestVersion":1}'),
    Buffer.from('{"source":{"commit":"a","commit":"b"}}'), Buffer.from([0xff]),
    Buffer.from([0xef, 0xbb, 0xbf, 0x7b, 0x7d]), Buffer.from('[]'), Buffer.from('null'),
    Buffer.from('{"number":1.5}'), Buffer.from('{"bad":"\\ud800"}')]) {
    const root = candidateCheckout(t);
    writeFileSync(join(root, MANIFEST), raw);
    rejects(() => verifyCandidate({ root }), 'invalid_manifest');
  }
});

test('candidate reads and nesting are finite, including changed giant components', async t => {
  const { verifyCandidate } = await verifier();
  for (const raw of [Buffer.alloc(64 * 1024 + 1, 32), Buffer.from('['.repeat(65) + '0' + ']'.repeat(65))]) {
    const root = candidateCheckout(t);
    writeFileSync(join(root, MANIFEST), raw);
    rejects(() => verifyCandidate({ root }), 'limit_exceeded');
  }
  const root = candidateCheckout(t);
  writeFileSync(join(root, 'SPEC.md'), Buffer.alloc(1024 * 1024 + 1));
  rejects(() => verifyCandidate({ root }), 'limit_exceeded');
});

test('candidate CLI works outside the checkout and fails closed without echoing supplied arguments', async t => {
  await verifier();
  const root = candidateCheckout(t);
  const cli = join(ROOT, 'scripts/verify-candidate.mjs');
  const run = args => spawnSync(process.execPath, [cli, ...args], {
    cwd: dirname(root), encoding: 'utf8', timeout: 10000,
  });
  const valid = run(['--root', root]);
  assert.equal(valid.status, 0, valid.stderr);
  assert.equal(valid.stderr, '');
  assert.equal(JSON.parse(valid.stdout).status, 'candidate_integrity_checked');
  for (const args of [['--network', 'synthetic-private-marker'], ['--root'], ['--root', root, '--root', root]]) {
    const invalid = run(args);
    assert.equal(invalid.status, 2);
    assert.equal(invalid.stdout, '');
    assert.equal(JSON.parse(invalid.stderr).reason, 'invalid_arguments');
    assert.ok(!invalid.stderr.includes('synthetic-private-marker'));
  }
  rmSync(join(root, 'SPEC.md'));
  const missing = run(['--root', root]);
  assert.equal(missing.status, 2);
  assert.equal(missing.stdout, '');
  assert.equal(JSON.parse(missing.stderr).reason, 'missing_path');
});
