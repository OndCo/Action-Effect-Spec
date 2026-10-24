import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = fileURLToPath(new URL('../../', import.meta.url));
export const MATRIX = 'conformance/core-accountability.json';
export const MANIFEST = 'profiles/github-issue-comment/candidate/manifest.json';
export const COMPONENTS = ['SPEC.md', 'schemas/effect-description.schema.json',
  'profiles/github-issue-comment/profile.json', 'profiles/github-issue-comment/README.md'];
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export const json = (root, path) => JSON.parse(readFileSync(join(root, path), 'utf8'));
export const writeJSON = (root, path, value) => writeFileSync(join(root, path), JSON.stringify(value, null, 2) + '\n');

export async function implementation(name, exported) {
  let module;
  try { module = await import(`../${name}.mjs`); }
  catch (error) { assert.fail(`${name} sidecar is not implemented: ${error.code ?? error.message}`); }
  assert.equal(typeof module[exported], 'function');
  return module;
}

export function sandbox(t, paths) {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'effect-sidecar-')));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const path of paths) {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    copyFileSync(join(ROOT, path), join(root, path));
  }
  return root;
}

export function candidateCheckout(t) {
  return sandbox(t, [MANIFEST, ...COMPONENTS]);
}

export function coverageCheckout(t) {
  const matrix = json(ROOT, MATRIX);
  return sandbox(t, [MATRIX, ...Object.values(matrix.files)
    .filter(file => file.repository === 'spec').map(file => file.path)]);
}

export function rejects(fn, reason) {
  assert.throws(fn, error => error.code === reason,
    `Expected a bounded sidecar rejection: ${reason}`);
}
