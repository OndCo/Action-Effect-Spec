import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { InputError, canonicalBytes, parseStrict } from './strict-json.mjs';
import { absoluteUri, compileBundledSchema, isObject, isString } from './schema.mjs';

export const SPEC_VERSION = '0.1.0-draft.1';
export const PROFILE_ID = 'https://example.org/profiles/refund/0.1.0-draft.1';
export const PROFILE_HASH = 'dddac40519b57620ca8b6fec558746ed8fb1f6ddf77263fd93cf5b2b582f2e00';
const AMOUNT = 'https://example.org/quantities/amount';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const digest = value => sha(canonicalBytes(value));
const result = (status, reason) => ({ status, reason, authority: 'not_evaluated' });
const stop = (status, reason) => { throw new InputError(status, reason); };
const bundled = path => parseStrict(readFileSync(new URL(`../../${path}`, import.meta.url)));
const validateStructure = compileBundledSchema(bundled('schemas/effect-description.schema.json'));

function references(doc) {
  const effects = new Map();
  const evidence = new Set();
  const bad = () => stop('invalid_input', 'references');
  for (const effect of doc.effects) {
    if (effects.has(effect.effect_id)) bad();
    const names = new Set(effect.quantities.map(q => q.name));
    if (names.size !== effect.quantities.length) bad();
    effects.set(effect.effect_id, names);
  }
  for (const item of doc.evidence) {
    if (evidence.has(item.evidence_id)) bad();
    evidence.add(item.evidence_id);
  }
  for (const ref of [...doc.coverage.evidence_refs,
    ...doc.effects.flatMap(e => e.evidence_refs), ...doc.relations.flatMap(r => r.evidence_refs)]) {
    if (!evidence.has(ref)) bad();
  }
  for (const relation of doc.relations) {
    if (!effects.has(relation.from) || !effects.has(relation.to)) bad();
  }
  const unknown = new Set();
  for (const item of doc.unknowns) {
    if (item.code !== 'unknown_quantity') continue;
    const { effect_id: id, quantity_name: name } = item.target;
    const key = JSON.stringify([id, name]);
    if (!effects.has(id) || name !== AMOUNT || effects.get(id).has(name) || unknown.has(key)) bad();
    unknown.add(key);
  }
}

function bindArtifacts(doc, profile, basis) {
  const bad = () => stop('untrusted_evidence', 'artifact_binding');
  for (const field of ['invocation', 'implementation', 'context']) {
    const row = profile.reference_resolution.find(r => r.field === `${field}.reference`);
    if (doc[field].reference !== row.reference || doc[field].digest.value !== digest(basis[row.member])) bad();
  }
  const row = profile.reference_resolution.find(r => r.field === 'mapping.id');
  if (doc.mapping.id !== row.reference || doc.mapping.revision !== row.revision
    || doc.mapping.digest.value !== digest(basis[row.member])) bad();
  const artifact = profile.reference_resolution.find(r => r.field === 'evidence.artifact_ref');
  for (const item of doc.evidence) {
    if (item.artifact_ref !== artifact.reference || item.artifact_digest.value !== digest(basis[artifact.member])
      || item.source !== basis.declaration.issuer) bad();
  }
}

function projection(doc, basis) {
  const { input, implementation, context, mapping, declaration } = basis;
  const applicable = input.operation === 'refund' && isString(input.order) && input.currency === 'USD'
    && implementation.name === 'synthetic-refund-tool' && implementation.version === '1.0.0'
    && implementation.visibility === 'declared' && isString(context.account)
    && context.destination === 'original-payment' && context.environment === 'synthetic'
    && mapping.id === 'https://example.org/mappings/refund' && mapping.revision === '1'
    && absoluteUri(declaration.issuer);
  const hasAmount = Object.hasOwn(input, 'amount_minor');
  if (!applicable || (hasAmount && !(typeof input.amount_minor === 'string'
    && /^(0|[1-9][0-9]{0,11})$/.test(input.amount_minor)
    && BigInt(input.amount_minor) <= 999999999999n))) stop('untrusted_evidence', 'applicability');
  const mismatch = () => stop('untrusted_evidence', 'effect_projection');
  if (doc.effects.length !== 1) mismatch();
  const effect = doc.effects[0];
  const unknownAmounts = doc.unknowns.filter(u => u.code === 'unknown_quantity');
  if (!effect.quantities.some(quantity => quantity.name === AMOUNT) && unknownAmounts.length === 0) {
    stop('invalid_input', 'structure');
  }
  if (doc.relations.length !== 0
    || doc.coverage.evidence_refs.length === 0
    || !doc.unknowns.some(item => item.code === 'unobserved_descendants')) mismatch();
  const slot = (actual, namespace, value) => actual.state === 'known' && actual.namespace === namespace && actual.value === value;
  if (effect.category !== 'https://example.org/effects/funds-transfer/1'
    || effect.operation !== 'https://example.org/operations/refund/1'
    || !slot(effect.resource, 'https://example.org/resource-types/order', input.order)
    || !slot(effect.destination, 'https://example.org/destination-types/payment', context.destination)
    || !slot(effect.data_class, 'https://example.org/classification', 'synthetic-transaction')
    || Object.hasOwn(effect, 'occurrence_ref') || effect.evidence_refs.length === 0) mismatch();
  if (hasAmount) {
    if (effect.quantities.length !== 1 || unknownAmounts.length !== 0) mismatch();
    const quantity = effect.quantities[0];
    if (quantity.name !== AMOUNT || quantity.value !== input.amount_minor
      || quantity.unit !== 'USD' || quantity.scale !== '2') mismatch();
  } else {
    if (effect.quantities.length !== 0 || unknownAmounts.length !== 1) mismatch();
  }
}

export function createConsumer(options = {}) {
  const profile = parseStrict(canonicalBytes(options.profile ?? bundled('examples/refund-profile.json')));
  const basis = parseStrict(canonicalBytes(options.basis ?? bundled('examples/synthetic-basis.json')));
  if (profile.id !== PROFILE_ID || digest(profile) !== PROFILE_HASH) throw new Error('Invalid pinned profile configuration');
  if (!isObject(basis) || ['input', 'implementation', 'context', 'mapping', 'declaration'].some(k => !isObject(basis[k]))) {
    throw new Error('Invalid basis configuration');
  }
  // The closure holds a private startup snapshot, never caller-owned mutable data.
  return bytes => {
    try {
      const doc = parseStrict(bytes);
      if (!isObject(doc) || typeof doc.spec_version !== 'string') stop('invalid_input', 'structure');
      if (doc.spec_version !== SPEC_VERSION) stop('unsupported_profile', 'spec_version');
      if (!validateStructure(doc)) stop('invalid_input', 'structure');
      references(doc);
      if (doc.critical_extensions.length) stop('unsupported_profile', 'critical_extension');
      if (doc.profile !== PROFILE_ID) stop('unsupported_profile', 'profile');
      if (doc.profile_digest.value !== PROFILE_HASH) stop('untrusted_evidence', 'profile_binding');
      if (doc.coverage.scope !== 'direct' || doc.coverage.completeness !== 'partial'
        || doc.effects.some(e => e.modality !== 'may') || doc.evidence.some(e => e.kind !== 'declaration')) {
        stop('unsupported_profile', 'evidence_scope');
      }
      bindArtifacts(doc, profile, basis);
      projection(doc, basis);
      return { ...result('accepted_partial', 'declared_partial'), description_digest: digest(doc),
        effect_count: doc.effects.length, unresolved_count: doc.unknowns.length };
    } catch (error) {
      return error instanceof InputError ? result(error.status, error.reason) : result('evaluation_failure', 'internal_error');
    }
  };
}

export function canonicalResult(bytes) {
  try {
    const canonical = canonicalBytes(parseStrict(bytes));
    return { ...result('canonicalized', 'supported_subset'), canonical_b64: canonical.toString('base64'), sha256: sha(canonical) };
  } catch (error) {
    return error instanceof InputError ? result(error.status, error.reason) : result('evaluation_failure', 'internal_error');
  }
}

export function capabilities() {
  return { ...result('capabilities', 'offline_snapshot'), spec_version: SPEC_VERSION, profile: PROFILE_ID,
    numeric_domain: 'safe_integer_tokens_only', acceptance_cache: false };
}
