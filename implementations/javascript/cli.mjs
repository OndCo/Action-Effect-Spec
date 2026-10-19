import { once } from 'node:events';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { capabilities, canonicalResult, createConsumer } from './consumer.mjs';
import { InputError, parseStrict } from './strict-json.mjs';
import { isObject } from './schema.mjs';

const FRAME_LIMIT = 2 * 1024 * 1024;
const failure = (status, reason) => ({ id: null, result: { status, reason, authority: 'not_evaluated' } });

export function handleFrame(frame, check) {
  let request;
  let document;
  try {
    request = parseStrict(frame, FRAME_LIMIT);
    if (!isObject(request) || typeof request.id !== 'string' || [...request.id].length < 1
      || [...request.id].length > 128 || !['hello', 'check', 'canonicalize'].includes(request.op)) {
      return failure('invalid_input', 'transport');
    }
    const keys = request.op === 'hello' ? ['id', 'op'] : ['id', 'op', 'document_b64'];
    if (Object.keys(request).length !== keys.length || keys.some(key => !Object.hasOwn(request, key))) {
      return failure('invalid_input', 'transport');
    }
    if (request.op !== 'hello') {
      if (typeof request.document_b64 !== 'string'
        || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(request.document_b64)) {
        return failure('invalid_input', 'transport');
      }
      document = Buffer.from(request.document_b64, 'base64');
      if (document.toString('base64') !== request.document_b64) return failure('invalid_input', 'transport');
    }
  } catch (error) {
    return error instanceof InputError ? failure('invalid_input', 'transport') : failure('evaluation_failure', 'internal_error');
  }
  try {
    if (request.op === 'hello') return { id: request.id, result: capabilities() };
    return { id: request.id, result: request.op === 'check' ? check(document) : canonicalResult(document) };
  } catch {
    return { ...failure('evaluation_failure', 'internal_error'), id: request.id };
  }
}

async function emit(row) {
  if (!process.stdout.write(JSON.stringify(row) + '\n')) await once(process.stdout, 'drain');
}

async function main() {
  let check;
  try {
    const args = process.argv.slice(2);
    if (args.length !== 0 && !(args.length === 2 && args[0] === '--basis' && args[1])) throw new Error('arguments');
    check = args.length ? createConsumer({ basis: parseStrict(readFileSync(args[1])) }) : createConsumer();
  } catch {
    process.stderr.write('Unable to initialize offline consumer; check local configuration and arguments.\n');
    process.exitCode = 2;
    return;
  }
  let parts = [];
  let size = 0;
  let oversized = false;
  async function finish() {
    await emit(oversized ? failure('evaluation_failure', 'limit_exceeded') : handleFrame(Buffer.concat(parts, size), check));
    parts = [];
    size = 0;
    oversized = false;
  }
  function append(bytes) {
    if (oversized) return;
    if (size + bytes.length > FRAME_LIMIT) {
      parts = [];
      size = 0;
      oversized = true;
    } else if (bytes.length) {
      parts.push(bytes);
      size += bytes.length;
    }
  }
  for await (const chunk of process.stdin) {
    let start = 0;
    for (let newline = chunk.indexOf(10, start); newline !== -1; newline = chunk.indexOf(10, start)) {
      append(chunk.subarray(start, newline));
      await finish();
      start = newline + 1;
    }
    append(chunk.subarray(start));
  }
  if (oversized || size > 0) await finish();
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  main().catch(() => {
    process.stderr.write('Offline consumer transport failed.\n');
    process.exitCode = 2;
  });
}
