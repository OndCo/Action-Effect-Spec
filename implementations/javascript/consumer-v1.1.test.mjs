import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { capabilities, canonicalResult, createConsumer } from './consumer.mjs';
import { handleFrame } from './cli.mjs';

const V1 = 'offline-consumer-v1';
const V11 = 'offline-consumer-v1.1';
const AMOUNT = 'https://example.org/quantities/amount';
const SECRET = 'synthetic-private-marker-do-not-echo';
const bytes = value => Buffer.from(JSON.stringify(value));
const fixture = name => JSON.parse(readFileSync(new URL(`../../examples/${name}.json`, import.meta.url)));
const basis = () => fixture('synthetic-basis');
const example = () => fixture('partial-refund');
const failure = (status, reason) => ({ status, reason, authority: 'not_evaluated' });
const HELLO = { ...failure('capabilities', 'offline_snapshot'), spec_version: '0.1.0-draft.1',
  profile: 'https://example.org/profiles/refund/0.1.0-draft.1',
  numeric_domain: 'safe_integer_tokens_only', acceptance_cache: false };
const HELLO_V11 = { ...HELLO, contract: V11 };
const ACCEPTED = { ...failure('accepted_partial', 'declared_partial'),
  description_digest: 'a357beff955d1372cb7aede84dd1b1baaa4c375008672c821bdbae1e27f62377',
  effect_count: 1, unresolved_count: 1 };
const CANONICAL = { ...failure('canonicalized', 'supported_subset'),
  canonical_b64: 'eyJhIjpbdHJ1ZSxudWxsXSwieiI6MH0=',
  sha256: '4097289243fbf05814aa5d808b55f34ed4f900c17916bdb8f636eb04ea630ae8' };

function fixtureDigest(value) {
  // An oracle for these ASCII-keyed fixtures, independent of consumer canonicalization.
  const sorted = item => Array.isArray(item) ? item.map(sorted)
    : item !== null && typeof item === 'object'
      ? Object.fromEntries(Object.keys(item).sort().map(key => [key, sorted(item[key])])) : item;
  return createHash('sha256').update(bytes(sorted(value))).digest('hex');
}

function bound(fixture, document = example()) {
  const doc = structuredClone(document);
  for (const [field, member] of [['invocation', 'input'], ['implementation', 'implementation'],
    ['context', 'context'], ['mapping', 'mapping']]) doc[field].digest.value = fixtureDigest(fixture[member]);
  for (const evidence of doc.evidence) {
    evidence.artifact_digest.value = fixtureDigest(fixture.declaration);
    evidence.source = fixture.declaration.issuer;
  }
  return doc;
}

function unknownAmount(doc) {
  doc.effects[0].quantities = [];
  doc.unknowns.push({ code: 'unknown_quantity', scope: 'amount unavailable',
    target: { effect_id: doc.effects[0].effect_id, quantity_name: AMOUNT } });
  return doc;
}

const selected = fixture => createConsumer({ contract: V11, basis: fixture ?? basis() });
const check = (doc, fixture) => selected(fixture)(bytes(doc));
const request = (op = 'hello', raw = bytes(example()), id = 'case') =>
  bytes(op === 'hello' ? { id, op } : { id, op, document_b64: raw.toString('base64') });
const cli = fileURLToPath(new URL('./cli.mjs', import.meta.url));
const execute = (input, args = []) => spawnSync(process.execPath, [cli, ...args], {
  input, cwd: tmpdir(), encoding: 'utf8', timeout: 10000, maxBuffer: 5 * 1024 * 1024
});
const stream = frames => Buffer.from(frames.map(frame => frame.toString()).join('\n'));

function successful(process, rows) {
  assert.equal(process.error, undefined);
  assert.equal(process.status, 0, process.stderr);
  assert.equal(process.stderr, '');
  assert.equal(process.stdout, rows.map(row => JSON.stringify(row) + '\n').join(''));
}

function fatal(process) {
  assert.equal(process.error, undefined);
  assert.equal(process.status, 2);
  assert.equal(process.stdout, '');
  assert.ok(process.stderr.length > 0);
  assert.ok(!process.stderr.includes(SECRET));
  assert.ok(!process.stderr.includes('Traceback') && !process.stderr.includes(' at '));
}

test('v1.1 API and adapter hello identify the contract, not a new wire schema', () => {
  assert.deepEqual(capabilities({ contract: V11 }), HELLO_V11);
  assert.deepEqual(handleFrame(request(), selected(), { contract: V11 }), { id: 'case', result: HELLO_V11 });
  assert.deepEqual(check(example()), ACCEPTED);
});

test('default and explicit v1 APIs preserve exact results and legacy null fallback', () => {
  for (const options of [{}, { contract: V1 }, { basis: null, profile: null }]) {
    assert.deepEqual(capabilities(options), HELLO);
    assert.deepEqual(createConsumer(options)(bytes(example())), ACCEPTED);
  }
  assert.deepEqual(canonicalResult(Buffer.from('{"z":-0,"a":[true,null]}')), CANONICAL);
});

test('bad API contract values throw sanitized startup errors instead of falling back', () => {
  for (const contract of [SECRET, '', null, true, 1, [], { secret: SECRET }]) {
    for (const create of [createConsumer, capabilities]) {
      assert.throws(() => create({ contract }), error =>
        /contract/i.test(error.message) && !error.message.includes(SECRET));
    }
  }
});

test('v1.1 rejects explicit nonobject basis/profile selections, including nullish ones', () => {
  for (const field of ['basis', 'profile']) {
    for (const value of [null, undefined, [], false, 0, SECRET]) {
      assert.throws(() => createConsumer({ contract: V11, [field]: value }));
    }
  }
  assert.deepEqual(createConsumer({ contract: V11 })(bytes(example())), ACCEPTED);
});

test('missing or nonobject selected fixture members are startup errors', () => {
  for (const member of ['input', 'implementation', 'context', 'mapping', 'declaration']) {
    for (const value of [undefined, null, [], false, 0, SECRET]) {
      const fixture = basis();
      if (value === undefined) delete fixture[member];
      else fixture[member] = value;
      assert.throws(() => selected(fixture), error => !error.message.includes(SECRET));
    }
  }
});

test('unsupported fixture scalars and absent nested fields load but fail applicability', () => {
  const changes = [['input', 'operation', 'charge'], ['input', 'order', null], ['input', 'order', ''],
    ['input', 'currency', 'EUR'], ['implementation', 'name', 'other-tool'],
    ['implementation', 'version', '2'], ['implementation', 'visibility', 'measured'],
    ['context', 'account', false], ['context', 'destination', 'other'],
    ['context', 'environment', 'production'], ['mapping', 'id', 'urn:other'], ['mapping', 'revision', '2']];
  for (const amount of [null, true, 7300, '-0', '-1', '00', '1e2', '1.0', '1\n', '1000000000000']) {
    changes.push(['input', 'amount_minor', amount]);
  }
  for (const [member, key] of [['input', 'order'], ['implementation', 'version'],
    ['context', 'account'], ['mapping', 'revision']]) changes.push([member, key, undefined]);
  for (const [member, key, value] of changes) {
    const fixture = basis();
    if (value === undefined) delete fixture[member][key];
    else fixture[member][key] = value;
    assert.deepEqual(check(bound(fixture), fixture), failure('untrusted_evidence', 'applicability'), `${member}.${key}`);
  }
});

test('empty fixture objects load; issuer applicability does not bypass earlier evidence checks', () => {
  for (const member of ['input', 'implementation', 'context', 'mapping', 'declaration']) {
    const fixture = basis();
    fixture[member] = {};
    const doc = example();
    doc.evidence = [];
    doc.coverage.evidence_refs = [];
    doc.effects[0].evidence_refs = [];
    assert.deepEqual(check(bound(fixture, doc), fixture), failure('untrusted_evidence', 'applicability'));
  }
  const fixture = basis();
  fixture.declaration.issuer = SECRET;
  assert.deepEqual(check(bound(fixture), fixture), failure('invalid_input', 'structure'));
  const doc = bound(fixture);
  doc.evidence[0].source = 'urn:other-issuer';
  assert.deepEqual(check(doc, fixture), failure('untrusted_evidence', 'artifact_binding'));
  doc.evidence = [];
  doc.coverage.evidence_refs = [];
  doc.effects[0].evidence_refs = [];
  assert.deepEqual(check(doc, fixture), failure('untrusted_evidence', 'applicability'));
});

const residuals = [
  ['category', d => { d.effects[0].category = 'urn:wrong'; }],
  ['operation', d => { d.effects[0].operation = 'urn:wrong'; }],
  ['resource', d => { d.effects[0].resource.value = 'another-order'; }],
  ['destination', d => { d.effects[0].destination.value = 'another-payment'; }],
  ['data class', d => { d.effects[0].data_class.value = 'another-class'; }],
  ['occurrence', d => { d.effects[0].occurrence_ref = 'not-observed'; }],
  ['relations', d => { d.relations = [{ from: 'effect-1', to: 'effect-1', kind: 'urn:relation', evidence_refs: ['decl-1'] }]; }],
  ['coverage evidence', d => { d.coverage.evidence_refs = []; }],
  ['effect evidence', d => { d.effects[0].evidence_refs = []; }],
  ['descendants', d => { d.unknowns = []; }]
];

test('paired defects: applicability precedes each later projection class', () => {
  const defects = [
    ['cardinality', d => { d.effects = []; }, 'untrusted_evidence', 'effect_projection'],
    ['missing amount', d => { d.effects[0].quantities = []; }, 'invalid_input', 'structure'],
    ['coupled mismatch', residuals[2][1], 'untrusted_evidence', 'effect_projection']
  ];
  for (const [label, mutate, status, reason] of defects) {
    const fixture = basis();
    fixture.input.currency = 'EUR';
    const doc = bound(fixture);
    mutate(doc);
    assert.deepEqual(check(doc, fixture), failure('untrusted_evidence', 'applicability'), label);
    fixture.input.currency = 'USD';
    assert.deepEqual(check(bound(fixture, doc), fixture), failure(status, reason), `repaired ${label}`);
  }
});

test('paired defects: cardinality precedes missing amounts regardless of tuple order', () => {
  for (const reverse of [false, true]) {
    const doc = example();
    doc.effects[0].quantities = [];
    const other = structuredClone(example().effects[0]);
    other.effect_id = 'other-effect';
    doc.effects.push(other);
    if (reverse) doc.effects.reverse();
    assert.deepEqual(check(doc), failure('untrusted_evidence', 'effect_projection'));
    doc.effects = doc.effects.filter(effect => effect.effect_id === 'effect-1');
    assert.deepEqual(check(doc), failure('invalid_input', 'structure'));
    doc.effects[0].quantities = example().effects[0].quantities;
    assert.deepEqual(check(doc), ACCEPTED);
  }
});

test('paired defects: cardinality does not select a good tuple over a coupled mismatch', () => {
  const doc = example();
  doc.effects[0].destination.value = 'wrong-payment';
  doc.effects.push({ ...structuredClone(example().effects[0]), effect_id: 'other-effect' });
  assert.deepEqual(check(doc), failure('untrusted_evidence', 'effect_projection'));
  doc.effects.pop();
  assert.deepEqual(check(doc), failure('untrusted_evidence', 'effect_projection'));
  doc.effects[0].destination.value = 'original-payment';
  assert.deepEqual(check(doc), ACCEPTED);
});

for (const [label, mutate] of residuals) {
  test(`paired defects: missing amount representation precedes ${label}`, () => {
    for (const amountPresent of [true, false]) {
      for (const unrelatedQuantity of [false, true]) {
        const fixture = basis();
        if (!amountPresent) delete fixture.input.amount_minor;
        const doc = bound(fixture);
        doc.effects[0].quantities = unrelatedQuantity
          ? [{ name: 'urn:other-quantity', value: '1', unit: 'USD', scale: '2' }] : [];
        mutate(doc);
        assert.deepEqual(check(doc, fixture), failure('invalid_input', 'structure'));
        if (amountPresent) doc.effects[0].quantities = example().effects[0].quantities;
        else unknownAmount(doc);
        assert.deepEqual(check(doc, fixture), failure('untrusted_evidence', 'effect_projection'));
      }
    }
  });
}

test('represented wrong amounts and other coupled defects stay projection mismatches', () => {
  for (const [key, value] of [['value', '7301'], ['unit', 'EUR'], ['scale', '3']]) {
    const doc = example();
    doc.effects[0].quantities[0][key] = value;
    doc.effects[0].resource.value = 'wrong';
    assert.deepEqual(check(doc), failure('untrusted_evidence', 'effect_projection'));
    doc.effects[0].resource.value = 'order-42';
    assert.deepEqual(check(doc), failure('untrusted_evidence', 'effect_projection'));
  }
  assert.deepEqual(check(unknownAmount(example())), failure('untrusted_evidence', 'effect_projection'));
  const fixture = basis();
  delete fixture.input.amount_minor;
  assert.deepEqual(check(bound(fixture), fixture), failure('untrusted_evidence', 'effect_projection'));
  const doc = unknownAmount(bound(fixture));
  assert.deepEqual(check(doc, fixture), { ...ACCEPTED, description_digest: fixtureDigest(doc), unresolved_count: 2 });
});

test('earlier document gates still precede final applicability and missing amounts', () => {
  const fixture = basis();
  fixture.input.currency = 'EUR';
  const cases = [
    [d => { d.contract = V11; }, 'invalid_input', 'structure'],
    [d => { d.unknowns.push({ code: 'unknown_quantity', scope: 'bad target', target: { effect_id: 'absent', quantity_name: AMOUNT } }); }, 'invalid_input', 'references'],
    [d => { d.critical_extensions = ['urn:critical:unknown']; }, 'unsupported_profile', 'critical_extension'],
    [d => { d.profile = 'urn:unknown-profile'; }, 'unsupported_profile', 'profile'],
    [d => { d.profile_digest.value = '0'.repeat(64); }, 'untrusted_evidence', 'profile_binding'],
    [d => { d.coverage.scope = 'transitive'; }, 'unsupported_profile', 'evidence_scope'],
    [d => { d.invocation.digest.value = '0'.repeat(64); }, 'untrusted_evidence', 'artifact_binding']
  ];
  for (const [mutate, status, reason] of cases) {
    const doc = bound(fixture);
    doc.effects[0].quantities = [];
    mutate(doc);
    assert.deepEqual(check(doc, fixture), failure(status, reason));
  }
});

test('default stdout transcript is byte-compatible; only opt-in hello adds contract', () => {
  const input = stream([request(), request('check'), request('canonicalize', Buffer.from('{"z":-0,"a":[true,null]}')),
    Buffer.from('not-json'), request('check', Buffer.from('{"spec_version":"future"}')),
    request('check', Buffer.from(SECRET))]);
  const rows = [{ id: 'case', result: HELLO }, { id: 'case', result: ACCEPTED }, { id: 'case', result: CANONICAL },
    { id: null, result: failure('invalid_input', 'transport') },
    { id: 'case', result: failure('unsupported_profile', 'spec_version') },
    { id: 'case', result: failure('invalid_input', 'syntax') }];
  successful(execute(input), rows);
  successful(execute(input, ['--contract', V1]), rows);
  successful(execute(input, ['--contract', V11]), [{ id: 'case', result: HELLO_V11 }, ...rows.slice(1)]);
});

test('v1.1 rejects unknown/malformed frames and documents, then continues serving', () => {
  const badFrames = [bytes({ id: 'case', op: SECRET }), Buffer.from('{"id":"a","id":"b","op":"hello"}'),
    bytes({ id: 'case', op: 'check', document_b64: 'e31=' }), bytes({ id: 'case', op: 'hello', contract: V1 })];
  const documents = [
    [Buffer.from('{"a":1,"a":2}'), 'invalid_input', 'syntax'],
    [Buffer.from([0xff]), 'invalid_input', 'syntax'],
    [Buffer.from('{"spec_version":"future","n":1.5,}'), 'invalid_input', 'syntax'],
    [Buffer.from('1.5'), 'unsupported_profile', 'numeric_domain'],
    [Buffer.from('null'), 'invalid_input', 'structure'],
    [bytes({ spec_version: V11 }), 'unsupported_profile', 'spec_version']
  ];
  const input = stream([...badFrames, ...documents.map(([raw]) => request('check', raw)), request()]);
  successful(execute(input, ['--contract', V11]), [
    ...badFrames.map(() => ({ id: null, result: failure('invalid_input', 'transport') })),
    ...documents.map(([, status, reason]) => ({ id: 'case', result: failure(status, reason) })),
    { id: 'case', result: HELLO_V11 }
  ]);
});

test('v1.1 preserves document/frame limits and recovery', () => {
  successful(execute(request(), ['--contract', V11]), [{ id: 'case', result: HELLO_V11 }]);
  const input = stream([Buffer.alloc(2 * 1024 * 1024 + 1, 32),
    request('check', Buffer.alloc(1024 * 1024 + 1, 32)), request()]);
  successful(execute(input, ['--contract', V11]), [
    { id: null, result: failure('evaluation_failure', 'limit_exceeded') },
    { id: 'case', result: failure('evaluation_failure', 'limit_exceeded') },
    { id: 'case', result: HELLO_V11 }
  ]);
});

test('contract and basis options compose in either order without changing applicability to startup failure', () => {
  const directory = mkdtempSync(join(tmpdir(), 'effect-v11-'));
  try {
    const path = join(directory, `${SECRET}.json`);
    const fixture = basis();
    fixture.input.currency = 'EUR';
    writeFileSync(path, bytes(fixture));
    const input = stream([request(), request('check', bytes(bound(fixture))), request('canonicalize', Buffer.from('{"z":-0,"a":[true,null]}'))]);
    for (const args of [['--contract', V11, '--basis', path], ['--basis', path, '--contract', V11]]) {
      successful(execute(input, args), [{ id: 'case', result: HELLO_V11 },
        { id: 'case', result: failure('untrusted_evidence', 'applicability') }, { id: 'case', result: CANONICAL }]);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('v1.1 startup failures are nonzero stderr only, with no fixture, path or request content', () => {
  successful(execute(request(), ['--contract', V11]), [{ id: 'case', result: HELLO_V11 }]);
  const directory = mkdtempSync(join(tmpdir(), 'effect-v11-'));
  try {
    const path = join(directory, `${SECRET}.json`);
    fatal(execute(request(), ['--contract', V11, '--basis', path]));
    const invalid = [Buffer.from(SECRET), Buffer.from('{"input":{},"input":{}}'), Buffer.from([0xff]),
      Buffer.from('{"n":1.5}'), Buffer.alloc(1024 * 1024 + 1, 32), ...[null, [], false, 0, SECRET].map(bytes)];
    for (const member of ['input', 'implementation', 'context', 'mapping', 'declaration']) {
      for (const value of [undefined, null, [], false, 0, SECRET]) {
        const fixture = basis();
        fixture.declaration.claim = SECRET;
        if (value === undefined) delete fixture[member];
        else fixture[member] = value;
        invalid.push(bytes(fixture));
      }
    }
    for (const raw of invalid) {
      writeFileSync(path, raw);
      fatal(execute(request('hello', undefined, SECRET), ['--contract', V11, '--basis', path]));
    }
    writeFileSync(path, 'null');
    successful(execute(request(), ['--basis', path]), [{ id: 'case', result: HELLO }]);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('bad contract options and ambiguous opt-in arguments fail without echoing supplied values', () => {
  for (const args of [['--contract', SECRET], ['--contract', ''], ['--contract'],
    ['--contract', V11, '--contract', V1], ['--contract', V11, '--basis'],
    ['--contract', V11, `--${SECRET}`], ['--contract', V11, SECRET]]) {
    fatal(execute(request(), args));
  }
});
