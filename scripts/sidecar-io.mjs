import { createHash } from 'node:crypto';
import { closeSync, constants, fstatSync, lstatSync, openSync, readSync, realpathSync } from 'node:fs';
import { isAbsolute, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { InputError, parseStrict } from '../implementations/javascript/strict-json.mjs';

export const REPO_ROOT = fileURLToPath(new URL('../', import.meta.url));
export const FILE_LIMIT = 1024 * 1024;
export const SHA256 = /^[0-9a-f]{64}$/;
export const REVISION = /^[0-9a-f]{40}$/;
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export const nonempty = value => typeof value === 'string' && value.trim().length > 0;
export const matches = (pattern, value) => typeof value === 'string' && pattern.test(value)
  && !value.endsWith('\n') && !value.endsWith('\r');

export class SidecarError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

export function requireThat(condition, code) {
  if (!condition) throw new SidecarError(code);
}

export function exactKeys(value, keys, code) {
  requireThat(isObject(value) && Object.keys(value).length === keys.length
    && keys.every(key => Object.hasOwn(value, key)), code);
}

export function stringList(value, { minimum = 0, maximum = 128, code } = {}) {
  requireThat(Array.isArray(value) && value.length >= minimum && value.length <= maximum
    && value.every(nonempty) && new Set(value).size === value.length, code);
}

export function relativePath(path) {
  requireThat(typeof path === 'string' && path.length <= 240 && !isAbsolute(path)
    && matches(/^[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)*$/, path)
    && path.split('/').every(part => part !== '.' && part !== '..'), 'unsafe_path');
  return path;
}

export function checkoutRoot(root) {
  try {
    requireThat(typeof root === 'string' && root.length > 0, 'unsafe_path');
    const absolute = resolve(root);
    const stat = lstatSync(absolute);
    requireThat(!stat.isSymbolicLink(), 'symlink_path');
    requireThat(stat.isDirectory(), 'not_directory');
    // The caller selects the trust root; macOS system aliases above it may resolve.
    return realpathSync(absolute);
  } catch (error) { throw fileError(error); }
}

function fileError(error) {
  if (error instanceof SidecarError) return error;
  if (error.code === 'ENOENT' || error.code === 'ENOTDIR') return new SidecarError('missing_path');
  if (error.code === 'ELOOP') return new SidecarError('symlink_path');
  return new SidecarError('unreadable_path');
}

export function readBounded(root, path, maximum = FILE_LIMIT) {
  relativePath(path);
  let descriptor;
  try {
    let current = root;
    const parts = path.split('/');
    let before;
    for (const [index, part] of parts.entries()) {
      current = join(current, part);
      before = lstatSync(current);
      requireThat(!before.isSymbolicLink(), 'symlink_path');
      requireThat(index === parts.length - 1 ? before.isFile() : before.isDirectory(),
        index === parts.length - 1 ? 'not_regular_file' : 'not_directory');
    }
    requireThat(realpathSync(current).startsWith(root + sep), 'unsafe_path');
    requireThat(before.size <= maximum, 'limit_exceeded');
    descriptor = openSync(current, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
    const opened = fstatSync(descriptor);
    requireThat(opened.isFile(), 'not_regular_file');
    requireThat(before.dev === opened.dev && before.ino === opened.ino, 'path_changed');
    requireThat(opened.size <= maximum, 'limit_exceeded');
    const bytes = Buffer.alloc(maximum + 1);
    let length = 0;
    while (length < bytes.length) {
      const count = readSync(descriptor, bytes, length, bytes.length - length, null);
      if (!count) break;
      length += count;
    }
    requireThat(length <= maximum, 'limit_exceeded');
    return bytes.subarray(0, length);
  } catch (error) { throw fileError(error); }
  finally { if (descriptor !== undefined) closeSync(descriptor); }
}

export function parseDocument(bytes, maximum, invalidCode) {
  try { return parseStrict(bytes, maximum); }
  catch (error) {
    if (error instanceof InputError && error.reason === 'limit_exceeded') throw new SidecarError('limit_exceeded');
    throw new SidecarError(invalidCode);
  }
}

export function runCLI(moduleURL, verify, failureStatus) {
  if (!process.argv[1]) return;
  let entry;
  try { entry = realpathSync(process.argv[1]); } catch { return; }
  if (entry !== fileURLToPath(moduleURL)) return;
  try {
    const args = process.argv.slice(2);
    requireThat(args.length === 0 || (args.length === 2 && args[0] === '--root' && nonempty(args[1])),
      'invalid_arguments');
    const result = verify(args.length ? { root: args[1] } : {});
    process.stdout.write(JSON.stringify(result) + '\n');
  } catch (error) {
    const reason = error instanceof SidecarError ? error.code : 'internal_error';
    process.stderr.write(JSON.stringify({ status: failureStatus, reason, authority: 'not_evaluated' }) + '\n');
    process.exitCode = 2;
  }
}
