import { canonicalBytes } from '../implementations/javascript/strict-json.mjs';
import { REPO_ROOT, SHA256, REVISION, checkoutRoot, exactKeys, matches, nonempty,
  parseDocument, readBounded, relativePath, requireThat, runCLI, sha256, stringList } from './sidecar-io.mjs';

export const MANIFEST_PATH = 'profiles/github-issue-comment/candidate/manifest.json';
export const MANIFEST_SHA256 = '2c9afb7c2710d1d3303b9ac282a1fc302f69bf17a36108dd36e7e875b02c9289';
const MANIFEST_LIMIT = 64 * 1024;
const PROFILE_ID = 'https://github.com/OndCo/Action-Effect-Spec/blob/v0.2.0-draft.1/profiles/github-issue-comment/profile.json';
const COMPONENT_ROLES = {
  'SPEC.md': 'core-specification',
  'schemas/effect-description.schema.json': 'core-structure',
  'profiles/github-issue-comment/profile.json': 'domain-manifest',
  'profiles/github-issue-comment/README.md': 'domain-semantics',
};
const CLAIMS = { authority: 'not_evaluated', fullCoreConformance: false, stable: false,
  securityCertified: false, externallyIndependentEvaluations: 0 };
const invalid = condition => requireThat(condition, 'invalid_manifest');
const keys = (value, expected) => exactKeys(value, expected, 'invalid_manifest');

function validateManifest(manifest) {
  keys(manifest, ['manifestVersion', 'candidateId', 'status', 'source', 'profile', 'claims',
    'scope', 'compatibility', 'failureSemantics', 'hashRule', 'components']);
  requireThat(manifest.manifestVersion === 1, 'unsupported_manifest_version');
  invalid(manifest.candidateId === 'github-issue-comment-1-candidate.1' && manifest.status === 'candidate');
  invalid(manifest.hashRule === 'sha-256:raw-file-bytes');

  keys(manifest.source, ['repository', 'revision']);
  invalid(manifest.source.repository === 'https://github.com/OndCo/Action-Effect-Spec'
    && matches(REVISION, manifest.source.revision));
  keys(manifest.profile, ['id', 'version', 'coreSpec', 'mappingRevision', 'digest']);
  invalid(manifest.profile.id === PROFILE_ID && manifest.profile.version === 'github-issue-comment/1'
    && manifest.profile.coreSpec === '0.1.0-draft.1' && manifest.profile.mappingRevision === '1');
  keys(manifest.profile.digest, ['algorithm', 'preimage', 'value']);
  invalid(manifest.profile.digest.algorithm === 'sha-256' && nonempty(manifest.profile.digest.preimage)
    && matches(SHA256, manifest.profile.digest.value));
  keys(manifest.claims, Object.keys(CLAIMS));
  invalid(Object.entries(CLAIMS).every(([key, value]) => manifest.claims[key] === value));

  keys(manifest.scope, ['operation', 'modality', 'coverage', 'nativeLanes', 'identityComparison',
    'maximumBodyBytes', 'maximumIssueNumber', 'referenceResolution', 'unknownScope', 'exclusions']);
  invalid(manifest.scope.operation === 'create_issue_comment' && manifest.scope.modality === 'may'
    && manifest.scope.coverage === 'direct-partial' && manifest.scope.identityComparison === 'exact-case-sensitive'
    && manifest.scope.maximumBodyBytes === 8192 && manifest.scope.maximumIssueNumber === 2147483647
    && manifest.scope.referenceResolution === 'configured-local-complete-objects-no-network'
    && nonempty(manifest.scope.unknownScope));
  stringList(manifest.scope.nativeLanes, { minimum: 2, maximum: 2, code: 'invalid_manifest' });
  invalid(manifest.scope.nativeLanes[0] === 'sdk' && manifest.scope.nativeLanes[1] === 'mcp');
  stringList(manifest.scope.exclusions, { minimum: 1, maximum: 16, code: 'invalid_manifest' });

  keys(manifest.compatibility, ['replacesWireProfile', 'wireIdentifiers', 'refundContracts', 'profileDigest', 'candidateIdentity']);
  invalid(manifest.compatibility.replacesWireProfile === false);
  invalid(['wireIdentifiers', 'refundContracts', 'profileDigest', 'candidateIdentity']
    .every(key => nonempty(manifest.compatibility[key])));
  keys(manifest.failureSemantics, ['nativeShape', 'otherShapedMcpTool', 'missingContext', 'implementationBinding',
    'descriptionBinding', 'unknownCriticalExtension', 'requiredExtensionPayload', 'operationalFailure',
    'resourceLimit', 'acceptance', 'precedence']);
  invalid(Object.values(manifest.failureSemantics).every(nonempty));

  invalid(Array.isArray(manifest.components) && manifest.components.length === 4);
  const paths = new Set();
  for (const component of manifest.components) {
    keys(component, ['role', 'path', 'sha256']);
    relativePath(component.path);
    invalid(Object.hasOwn(COMPONENT_ROLES, component.path) && !paths.has(component.path)
      && component.role === COMPONENT_ROLES[component.path] && matches(SHA256, component.sha256));
    paths.add(component.path);
  }
}

export function verifyCandidate({ root = REPO_ROOT } = {}) {
  const base = checkoutRoot(root);
  const bytes = readBounded(base, MANIFEST_PATH, MANIFEST_LIMIT);
  const manifest = parseDocument(bytes, MANIFEST_LIMIT, 'invalid_manifest');
  validateManifest(manifest);
  // This pin is outside the manifest and its four components: no self-hash cycle.
  requireThat(sha256(bytes) === MANIFEST_SHA256, 'manifest_digest_mismatch');
  const components = new Map();
  for (const component of manifest.components) {
    const content = readBounded(base, component.path);
    requireThat(sha256(content) === component.sha256, 'component_digest_mismatch');
    components.set(component.path, content);
  }
  const profile = parseDocument(components.get('profiles/github-issue-comment/profile.json'),
    MANIFEST_LIMIT, 'invalid_manifest');
  invalid(profile.id === manifest.profile.id && profile.version === manifest.profile.version
    && profile.core_spec === manifest.profile.coreSpec && profile.mapping_revision === manifest.profile.mappingRevision
    && profile.authority === 'not_evaluated');
  requireThat(sha256(canonicalBytes(profile)) === manifest.profile.digest.value, 'profile_digest_mismatch');
  return { status: 'candidate_integrity_checked', candidateId: manifest.candidateId,
    profileVersion: profile.version, normativeComponentsChecked: components.size, ...CLAIMS, testsExecuted: 0 };
}

runCLI(import.meta.url, verifyCandidate, 'candidate_integrity_failed');
