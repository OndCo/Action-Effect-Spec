import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';

async function strictModule() {
  try { return await import('./strict-json.mjs'); }
  catch (error) { assert.fail(`Strict parser implementation unavailable: ${error.code ?? error.message}`); }
}

function failure(fn, status, reason) {
  assert.throws(fn, error => error.status === status && error.reason === reason);
}

test('duplicate decoded keys fail even when spelling differs', async () => {
  const { parseStrict } = await strictModule();
  failure(() => parseStrict(Buffer.from('{"a":1,"\\u0061":2}')), 'invalid_input', 'syntax');
});

test('syntax error takes precedence over unsupported numeric token', async () => {
  const { parseStrict } = await strictModule();
  failure(() => parseStrict(Buffer.from('{"a":1.5,"a":2}')), 'invalid_input', 'syntax');
});

test('invalid UTF-8, BOM and lone surrogate keys/values fail', async () => {
  const { parseStrict } = await strictModule();
  for (const input of [Buffer.from([0xff]), Buffer.from([0xef, 0xbb, 0xbf, 0x7b, 0x7d]),
    Buffer.from('"\\ud800"'), Buffer.from('{"\\udc00":"x"}')]) {
    failure(() => parseStrict(input), 'invalid_input', 'syntax');
  }
});

test('prototype-like keys remain inert own data', async () => {
  const { parseStrict, canonicalBytes } = await strictModule();
  const object = parseStrict(Buffer.from('{"__proto__":{"polluted":true},"constructor":"x"}'));
  assert.equal(Object.hasOwn(object, '__proto__'), true);
  assert.equal({}.polluted, undefined);
  assert.equal(canonicalBytes(object).toString(), '{"__proto__":{"polluted":true},"constructor":"x"}');
});

test('canonicalization sorts by UTF-16 code units, not code points', async () => {
  const { parseStrict, canonicalBytes } = await strictModule();
  const object = parseStrict(Buffer.from('{"\ue000":"bmp","\ud83d\ude00":"astral","a":"first"}'));
  assert.equal(canonicalBytes(object).toString(), '{"a":"first","\ud83d\ude00":"astral","\ue000":"bmp"}');
});

test('canonicalization preserves Unicode normalization differences', async () => {
  const { parseStrict, canonicalBytes } = await strictModule();
  const a = canonicalBytes(parseStrict(Buffer.from('"\u00e9"')));
  const b = canonicalBytes(parseStrict(Buffer.from('"e\u0301"')));
  assert.notDeepEqual(a, b);
});

test('canonical escaping and negative zero follow the supported JCS subset', async () => {
  const { parseStrict, canonicalBytes } = await strictModule();
  const bytes = canonicalBytes(parseStrict(Buffer.from('{ "z": -0, "a": "\\n\\t\\b\\f\\r\\\"\\\\/" }')));
  assert.equal(bytes.toString(), '{"a":"\\n\\t\\b\\f\\r\\\"\\\\/","z":0}');
  assert.equal(createHash('sha256').update(bytes).digest('hex').length, 64);
});

test('integer boundaries accepted and other valid numeric forms unsupported', async () => {
  const { parseStrict } = await strictModule();
  assert.equal(parseStrict(Buffer.from('9007199254740991')), 9007199254740991);
  assert.equal(parseStrict(Buffer.from('-9007199254740991')), -9007199254740991);
  for (const input of ['9007199254740992', '-9007199254740992', '1.0', '1e0', '1e999']) {
    failure(() => parseStrict(Buffer.from(input)), 'unsupported_profile', 'numeric_domain');
  }
});

test('malformed JSON tokens cannot be converted to numeric uncertainty', async () => {
  const { parseStrict } = await strictModule();
  for (const input of ['NaN', 'Infinity', '01', '[1,]', '{"a":}', 'true false', '"unterminated']) {
    failure(() => parseStrict(Buffer.from(input)), 'invalid_input', 'syntax');
  }
});

test('container depth 64 accepted, depth 65 explicitly fails', async () => {
  const { parseStrict } = await strictModule();
  assert.equal(Array.isArray(parseStrict(Buffer.from('['.repeat(64) + '0' + ']'.repeat(64)))), true);
  failure(() => parseStrict(Buffer.from('['.repeat(65) + '0' + ']'.repeat(65))), 'evaluation_failure', 'limit_exceeded');
});

test('oversized input is bounded before parsing', async () => {
  const { parseStrict } = await strictModule();
  failure(() => parseStrict(Buffer.alloc(1024 * 1024 + 1, 32)), 'evaluation_failure', 'limit_exceeded');
});

const fixture = name => JSON.parse(readFileSync(new URL(`../../examples/${name}`, import.meta.url), 'utf8'));
async function consumer(basis = fixture('synthetic-basis.json')) {
  let module;
  try { module = await import('./consumer.mjs'); }
  catch (error) { assert.fail(`Consumer implementation unavailable: ${error.code ?? error.message}`); }
  return module.createConsumer({ profile: fixture('refund-profile.json'), basis });
}
const asBytes = object => Buffer.from(JSON.stringify(object));
const minimalResult = (status, reason) => ({ status, reason, authority: 'not_evaluated' });

test('bound partial declaration accepted without a permission field', async () => {
  const run = await consumer();
  const result = run(asBytes(fixture('partial-refund.json')));
  assert.equal(result.status, 'accepted_partial');
  assert.equal(result.reason, 'declared_partial');
  assert.equal(result.authority, 'not_evaluated');
  assert.equal(result.effect_count, 1);
  assert.equal(result.unresolved_count, 1);
  assert.match(result.description_digest, /^[0-9a-f]{64}$/);
  assert.equal('allow' in result || 'decision' in result, false);
});

test('unsupported spec is different from malformed structure', async () => {
  const run = await consumer();
  const doc = fixture('partial-refund.json');
  doc.spec_version = '2.0';
  assert.deepEqual(run(asBytes(doc)), minimalResult('unsupported_profile', 'spec_version'));
  doc.spec_version = null;
  assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'));
});

test('extra fields, non-URI profiles and malformed quantity coefficients fail shape checks', async () => {
  const run = await consumer();
  const extra = fixture('partial-refund.json'); extra.allow = true;
  assert.deepEqual(run(asBytes(extra)), minimalResult('invalid_input', 'structure'));
  const uri = fixture('partial-refund.json'); uri.profile = 'relative';
  assert.deepEqual(run(asBytes(uri)), minimalResult('invalid_input', 'structure'));
  for (const value of ['-0', '01', '7.3e3', 7300]) {
    const doc = fixture('partial-refund.json'); doc.effects[0].quantities[0].value = value;
    assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'));
  }
});

test('effect and evidence IDs are unique and locally resolved', async () => {
  const run = await consumer();
  for (const field of ['effects', 'evidence']) {
    const doc = fixture('partial-refund.json'); doc[field].push(structuredClone(doc[field][0]));
    assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'references'));
  }
  const dangling = fixture('partial-refund.json'); dangling.effects[0].evidence_refs = ['external'];
  assert.deepEqual(run(asBytes(dangling)), minimalResult('invalid_input', 'references'));
});

test('quantity identities cannot duplicate or be both known and unknown', async () => {
  const run = await consumer();
  const repeated = fixture('partial-refund.json');
  repeated.effects[0].quantities.push(structuredClone(repeated.effects[0].quantities[0]));
  assert.deepEqual(run(asBytes(repeated)), minimalResult('invalid_input', 'references'));
  const collision = fixture('partial-refund.json');
  collision.unknowns.push({ code: 'unknown_quantity', scope: 'amount',
    target: { effect_id: 'effect-1', quantity_name: 'https://example.org/quantities/amount' } });
  assert.deepEqual(run(asBytes(collision)), minimalResult('invalid_input', 'references'));
});

test('critical extensions remain unsupported rather than silently ignored', async () => {
  const run = await consumer(); const doc = fixture('partial-refund.json');
  doc.critical_extensions = ['https://example.org/extensions/critical/1'];
  assert.deepEqual(run(asBytes(doc)), minimalResult('unsupported_profile', 'critical_extension'));
});

test('profile content is pinned, not trusted merely because the URI matches', async () => {
  const run = await consumer(); const doc = fixture('partial-refund.json');
  doc.profile_digest.value = '0'.repeat(64);
  assert.deepEqual(run(asBytes(doc)), minimalResult('untrusted_evidence', 'profile_binding'));
});

test('evidence references and digests both required', async () => {
  const run = await consumer();
  for (const field of ['artifact_ref', 'artifact_digest']) {
    const doc = fixture('partial-refund.json'); delete doc.evidence[0][field];
    assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'));
  }
});

test('bound components are recomputed, no remote references are followed', async () => {
  const run = await consumer();
  const badHash = fixture('partial-refund.json'); badHash.context.digest.value = '0'.repeat(64);
  assert.deepEqual(run(asBytes(badHash)), minimalResult('untrusted_evidence', 'artifact_binding'));
  const remote = fixture('partial-refund.json'); remote.context.reference = 'http://169.254.169.254/latest';
  assert.deepEqual(run(asBytes(remote)), minimalResult('untrusted_evidence', 'artifact_binding'));
});

test('destination, amount and currency changes fail the coupled projection', async () => {
  const run = await consumer();
  for (const mutate of [d => { d.effects[0].destination.value = 'attacker'; },
    d => { d.effects[0].quantities[0].value = '7400'; },
    d => { d.effects[0].quantities[0].unit = 'EUR'; }]) {
    const doc = fixture('partial-refund.json'); mutate(doc);
    assert.deepEqual(run(asBytes(doc)), minimalResult('untrusted_evidence', 'effect_projection'));
  }
});

test('missing required amount cannot silently mean zero', async () => {
  const run = await consumer(); const doc = fixture('partial-refund.json');
  doc.effects[0].quantities = [];
  assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'));
});

test('unknown amount is accepted only with matching missing-source and exact target', async () => {
  const basis = fixture('synthetic-basis.json'); delete basis.input.amount_minor;
  const doc = fixture('partial-refund.json'); doc.effects[0].quantities = [];
  doc.unknowns.push({ code: 'unknown_quantity', scope: 'amount unavailable',
    target: { effect_id: 'effect-1', quantity_name: 'https://example.org/quantities/amount' } });
  const { canonicalBytes } = await strictModule();
  doc.invocation.digest.value = createHash('sha256').update(canonicalBytes(basis.input)).digest('hex');
  const run = await consumer(basis);
  assert.equal(run(asBytes(doc)).status, 'accepted_partial');
  assert.equal(run(asBytes(doc)).unresolved_count, 2);
});

test('an explicit unknown against an available amount is disagreement, not absent structure', async () => {
  const run = await consumer();
  const doc = fixture('partial-refund.json');
  doc.effects[0].quantities = [];
  doc.unknowns.push({ code: 'unknown_quantity', scope: 'amount unavailable',
    target: { effect_id: 'effect-1', quantity_name: 'https://example.org/quantities/amount' } });
  assert.deepEqual(run(asBytes(doc)), minimalResult('untrusted_evidence', 'effect_projection'));
  doc.unknowns.pop();
  assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'));
  doc.effects[0].quantities = [{ name: 'urn:quantities:other', value: '7300', unit: 'USD', scale: '2' }];
  assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'));
});

test('URI syntax validates components without dereferencing or normalizing identifiers', async () => {
  const run = await consumer();
  for (const uri of ['https://[', 'https://example.org/#first#second', 'https://[not-ip]/',
    'https://a:b:c/', 'https://example.org:port/', 'https://user@@host/',
    'https://host/path[raw]', 'https://host/?q=[raw]', 'urn:value#bad#fragment',
    'https://[::1]suffix/', 'https://[vG.invalid]/', 'https://[fe80::1%25en0]/']) {
    const doc = fixture('partial-refund.json'); doc.record_id = uri;
    assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'), uri);
  }
  for (const uri of ['urn:example:one', 'mailto:operator@example.org', 'file:///tmp/example',
    'https://user:pass@[2001:db8::1]:443/path?q=a?b#frag', 'https://[vF.a:b]/',
    'https://host/%5Bencoded%5D?q=%23value#ok', 'custom:/a/b', 'custom:a:b@c']) {
    const doc = fixture('partial-refund.json'); doc.record_id = uri;
    assert.equal(run(asBytes(doc)).status, 'accepted_partial', uri);
  }
});

test('an observation or bound is explicitly outside this declaration profile', async () => {
  const run = await consumer();
  const bound = fixture('partial-refund.json'); bound.coverage.completeness = 'bounded_claim';
  assert.deepEqual(run(asBytes(bound)), minimalResult('unsupported_profile', 'evidence_scope'));
  const observed = fixture('partial-refund.json'); observed.effects[0].modality = 'observed';
  observed.effects[0].occurrence_ref = 'occurrence-1';
  assert.deepEqual(run(asBytes(observed)), minimalResult('unsupported_profile', 'evidence_scope'));
});

test('terminal newlines cannot exploit regex dollar anchors in URI or quantity fields', async () => {
  const run = await consumer();
  for (const mutate of [d => { d.record_id += '\n'; },
    d => { d.effects[0].quantities[0].value += '\n'; },
    d => { d.context.digest.value += '\n'; }, d => { d.effects[0].quantities[0].scale += '\n'; }]) {
    const doc = fixture('partial-refund.json'); mutate(doc);
    assert.deepEqual(run(asBytes(doc)), minimalResult('invalid_input', 'structure'));
  }
});
