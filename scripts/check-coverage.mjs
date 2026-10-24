import { REPO_ROOT, REVISION, SHA256, checkoutRoot, exactKeys, isObject, matches, nonempty,
  parseDocument, readBounded, relativePath, requireThat, runCLI, sha256, stringList } from './sidecar-io.mjs';

export const MATRIX_PATH = 'conformance/core-accountability.json';
const MATRIX_LIMIT = 512 * 1024;
const ROLES = ['producer', 'registry_publisher', 'evidence_checker', 'consumer', 'authority', 'enforcement_point', 'observer'];
const SUPPORT = ['supported_subset', 'partial', 'unsupported', 'not_applicable'];
const UNSUPPORTED = ['authority_grants', 'signatures', 'cel', 'current_revocation',
  'remote_registries', 'enforcement', 'provider_observation', 'transitive_bounds'];
const TARGETS = {
  javascript_refund: { repository: 'spec', roles: ['consumer', 'evidence_checker'],
    contracts: ['offline-consumer-v1', 'offline-consumer-v1.1'], profile: 'https://example.org/profiles/refund/0.1.0-draft.1' },
  python_refund: { repository: 'spec', roles: ['consumer', 'evidence_checker'],
    contracts: ['offline-consumer-v1', 'offline-consumer-v1.1'], profile: 'https://example.org/profiles/refund/0.1.0-draft.1' },
  github_domain: { repository: 'bench', roles: ['consumer', 'producer', 'evidence_checker'],
    contracts: ['github-issue-comment/1'],
    profile: 'https://github.com/OndCo/Action-Effect-Spec/blob/v0.2.0-draft.1/profiles/github-issue-comment/profile.json' },
};
const IDS = Array.from({ length: 28 }, (_, i) => `CORE-${String(i + 1).padStart(3, '0')}`);
const invalid = condition => requireThat(condition, 'invalid_coverage');
const keys = (value, expected) => exactKeys(value, expected, 'invalid_coverage');
const list = (value, minimum = 0, maximum = 128) => stringList(value, { minimum, maximum, code: 'invalid_coverage' });
const sameList = (actual, expected) => {
  list(actual, expected.length, expected.length);
  invalid(actual.every((value, index) => value === expected[index]));
};

function dictionary(value, maximum) {
  invalid(isObject(value) && Object.keys(value).length > 0 && Object.keys(value).length <= maximum);
}

function validateMatrix(matrix) {
  keys(matrix, ['format', 'spec', 'claims', 'roles', 'repositories', 'implementations', 'files', 'anchors', 'requirements']);
  invalid(matrix.format === 'core-accountability/1');
  keys(matrix.spec, ['path', 'version', 'revision']);
  invalid(matrix.spec.path === 'SPEC.md' && matrix.spec.version === '0.1.0-draft.1' && matches(REVISION, matrix.spec.revision));
  keys(matrix.claims, ['scope', 'fullCoreConformance', 'securityCertified', 'externallyIndependentEvaluations', 'testExecution']);
  invalid(matrix.claims.scope === 'partial' && matrix.claims.fullCoreConformance === false
    && matrix.claims.securityCertified === false && matrix.claims.externallyIndependentEvaluations === 0
    && matrix.claims.testExecution === 'not_performed_by_integrity_checker');
  keys(matrix.roles, ROLES);
  invalid(Object.values(matrix.roles).every(nonempty));
  keys(matrix.repositories, ['spec', 'bench']);
  for (const [id, repository] of Object.entries(matrix.repositories)) {
    keys(repository, ['url', 'revision', 'verification']);
    invalid(repository.url === `https://github.com/OndCo/Action-Effect-${id === 'spec' ? 'Spec' : 'Bench'}`
      && matches(REVISION, repository.revision)
      && repository.verification === (id === 'spec' ? 'local_file_integrity_only' : 'external_pinned_not_checked'));
  }
  invalid(matrix.spec.revision === matrix.repositories.spec.revision);
  keys(matrix.implementations, Object.keys(TARGETS));
  for (const [id, target] of Object.entries(matrix.implementations)) {
    keys(target, ['repository', 'roles', 'contracts', 'profile', 'authority', 'unsupportedCapabilities', 'scope']);
    const expected = TARGETS[id];
    invalid(target.repository === expected.repository && target.profile === expected.profile
      && target.authority === 'not_evaluated' && nonempty(target.scope));
    sameList(target.roles, expected.roles);
    sameList(target.contracts, expected.contracts);
    sameList(target.unsupportedCapabilities, UNSUPPORTED);
  }

  dictionary(matrix.files, 64);
  for (const file of Object.values(matrix.files)) {
    invalid(isObject(file) && ['spec', 'bench'].includes(file.repository));
    keys(file, file.repository === 'spec' ? ['repository', 'path', 'sha256'] : ['repository', 'path']);
    relativePath(file.path);
    if (file.repository === 'spec') invalid(matches(SHA256, file.sha256));
    else invalid(file.path.startsWith('runtime-pilot/'));
  }
  invalid(matrix.files.spec?.repository === 'spec' && matrix.files.spec.path === matrix.spec.path);
  dictionary(matrix.anchors, 256);
  for (const anchor of Object.values(matrix.anchors)) {
    keys(anchor, ['file', 'kind', 'selector']);
    invalid(typeof anchor.file === 'string' && Object.hasOwn(matrix.files, anchor.file) && ['implementation', 'test'].includes(anchor.kind)
      && nonempty(anchor.selector) && anchor.selector.length <= 1024 && !/[\r\n]/.test(anchor.selector));
    if (anchor.kind === 'test') {
      invalid(/^test\('[^']+',/.test(anchor.selector) || /^    def test_[A-Za-z0-9_]+\(self\):$/.test(anchor.selector));
    }
  }
  invalid(Array.isArray(matrix.requirements) && matrix.requirements.length === IDS.length);
  for (const [index, row] of matrix.requirements.entries()) {
    keys(row, ['id', 'obligation', 'normativeAnchor', 'accountableRoles', 'roleGaps', 'implementations']);
    invalid(row.id === IDS[index] && nonempty(row.obligation) && row.normativeAnchor === `**${row.id}:**`);
    list(row.accountableRoles, 1, ROLES.length);
    invalid(row.accountableRoles.every(role => ROLES.includes(role)));
    invalid(isObject(row.roleGaps) && Object.entries(row.roleGaps)
      .every(([role, gap]) => row.accountableRoles.includes(role) && nonempty(gap)));
    keys(row.implementations, Object.keys(TARGETS));
    for (const [id, assessment] of Object.entries(row.implementations)) {
      keys(assessment, ['roleSupport', 'scope', 'implementation', 'positive', 'negative', 'untested']);
      keys(assessment.roleSupport, TARGETS[id].roles);
      invalid(Object.values(assessment.roleSupport).every(status => SUPPORT.includes(status)) && nonempty(assessment.scope));
      list(assessment.untested, 1, 32);
      for (const field of ['implementation', 'positive', 'negative']) {
        list(assessment[field], 0, 32);
        for (const reference of assessment[field]) {
          invalid(Object.hasOwn(matrix.anchors, reference));
          const anchor = matrix.anchors[reference];
          invalid(anchor.kind === (field === 'implementation' ? 'implementation' : 'test')
            && matrix.files[anchor.file].repository === TARGETS[id].repository);
        }
      }
      if (Object.values(assessment.roleSupport).some(status => ['supported_subset', 'partial'].includes(status))) {
        invalid(assessment.implementation.length > 0);
      }
      if (Object.values(assessment.roleSupport).includes('supported_subset')) {
        invalid(assessment.positive.length > 0 && assessment.negative.length > 0);
      }
    }
    for (const role of row.accountableRoles) {
      invalid(Object.hasOwn(row.roleGaps, role) || Object.values(row.implementations)
        .some(assessment => Object.hasOwn(assessment.roleSupport, role) && assessment.roleSupport[role] !== 'not_applicable'));
    }
  }
}

export function checkCoverage({ root = REPO_ROOT } = {}) {
  const base = checkoutRoot(root);
  const matrix = parseDocument(readBounded(base, MATRIX_PATH, MATRIX_LIMIT), MATRIX_LIMIT, 'invalid_coverage');
  validateMatrix(matrix);
  const localFiles = new Map();
  for (const [id, file] of Object.entries(matrix.files)) {
    // A pinned Bench citation is deliberately not a local path or a network request.
    if (file.repository !== 'spec') continue;
    const bytes = readBounded(base, file.path);
    requireThat(sha256(bytes) === file.sha256, 'source_digest_mismatch');
    localFiles.set(id, bytes.toString('utf8'));
  }
  const normative = localFiles.get('spec');
  invalid(normative.includes(`Version \`${matrix.spec.version}\``));
  const coreIds = [...normative.matchAll(/\*\*(CORE-\d{3}):\*\*/g)].map(match => match[1]);
  sameList(coreIds, IDS);
  let localAnchorsChecked = IDS.length;
  let externalAnchorsUnchecked = 0;
  for (const anchor of Object.values(matrix.anchors)) {
    if (!localFiles.has(anchor.file)) {
      externalAnchorsUnchecked++;
      continue;
    }
    requireThat(localFiles.get(anchor.file).split(anchor.selector).length === 2, 'anchor_mismatch');
    localAnchorsChecked++;
  }
  return { status: 'coverage_integrity_checked', scope: 'partial', requirements: IDS.length,
    localFilesChecked: localFiles.size, localAnchorsChecked, externalAnchorsUnchecked,
    testsExecuted: 0, fullCoreConformance: false, externallyIndependentEvaluations: 0 };
}

runCLI(import.meta.url, checkCoverage, 'coverage_integrity_failed');
