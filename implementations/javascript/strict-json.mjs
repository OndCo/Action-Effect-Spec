export const DOCUMENT_LIMIT = 1024 * 1024;
export const DEPTH_LIMIT = 64;

export class InputError extends Error {
  constructor(status, reason) {
    super(reason);
    this.name = 'InputError';
    this.status = status;
    this.reason = reason;
  }
}

const syntax = () => { throw new InputError('invalid_input', 'syntax'); };
const limit = () => { throw new InputError('evaluation_failure', 'limit_exceeded'); };

export function scalarString(value) {
  if (typeof value !== 'string') return false;
  for (let i = 0; i < value.length; i++) {
    const code = value.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = value.charCodeAt(++i);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return false;
    } else if (code >= 0xdc00 && code <= 0xdfff) return false;
  }
  return true;
}

export function parseStrict(bytes, maxBytes = DOCUMENT_LIMIT) {
  if (!(bytes instanceof Uint8Array)) syntax();
  if (bytes.byteLength > maxBytes) limit();
  if (bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) syntax();
  let source;
  try { source = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes); }
  catch { syntax(); }
  let cursor = 0;
  let unsupportedNumber = false;
  const numeric = /-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/y;
  const whitespace = () => {
    while (cursor < source.length && ' \t\r\n'.includes(source[cursor])) cursor++;
  };
  function string() {
    if (source[cursor] !== '"') syntax();
    const start = cursor++;
    while (cursor < source.length) {
      if (source[cursor] === '\\') { cursor += 2; continue; }
      if (source[cursor++] !== '"') continue;
      let value;
      try { value = JSON.parse(source.slice(start, cursor)); }
      catch { syntax(); }
      if (!scalarString(value)) syntax();
      return value;
    }
    syntax();
  }
  function value(depth) {
    whitespace();
    const next = source[cursor];
    if (next === '"') return string();
    if (next === '{' || next === '[') {
      if (depth + 1 > DEPTH_LIMIT) limit();
      cursor++;
      const object = next === '{';
      const output = object ? Object.create(null) : [];
      const seen = new Set();
      const closing = object ? '}' : ']';
      whitespace();
      if (source[cursor] === closing) { cursor++; return output; }
      while (true) {
        if (object) {
          whitespace();
          const key = string();
          if (seen.has(key)) syntax();
          seen.add(key);
          whitespace();
          if (source[cursor++] !== ':') syntax();
          output[key] = value(depth + 1);
        } else output.push(value(depth + 1));
        whitespace();
        const separator = source[cursor++];
        if (separator === closing) return output;
        if (separator !== ',') syntax();
      }
    }
    for (const [token, result] of [['true', true], ['false', false], ['null', null]]) {
      if (source.startsWith(token, cursor)) { cursor += token.length; return result; }
    }
    numeric.lastIndex = cursor;
    const match = numeric.exec(source);
    if (!match) syntax();
    cursor = numeric.lastIndex;
    const token = match[0];
    // Finish syntax validation before reporting a supported-domain mismatch.
    if (/[.eE]/.test(token) || token.replace('-', '').length > 16) {
      unsupportedNumber = true;
      return 0;
    }
    const parsed = Number(token);
    if (!Number.isSafeInteger(parsed)) unsupportedNumber = true;
    return parsed;
  }
  const parsed = value(0);
  whitespace();
  if (cursor !== source.length) syntax();
  if (unsupportedNumber) throw new InputError('unsupported_profile', 'numeric_domain');
  return parsed;
}

export function canonicalBytes(value) {
  function encode(item, depth) {
    if (item === null) return 'null';
    if (typeof item === 'boolean') return item ? 'true' : 'false';
    if (typeof item === 'string') {
      if (!scalarString(item)) syntax();
      return JSON.stringify(item);
    }
    if (typeof item === 'number') {
      if (!Number.isSafeInteger(item)) throw new InputError('unsupported_profile', 'numeric_domain');
      return Object.is(item, -0) ? '0' : JSON.stringify(item);
    }
    if (!item || typeof item !== 'object') syntax();
    if (depth + 1 > DEPTH_LIMIT) limit();
    if (Array.isArray(item)) return `[${item.map(child => encode(child, depth + 1)).join(',')}]`;
    const members = Object.keys(item).sort().map(key => {
      if (!scalarString(key)) syntax();
      return `${JSON.stringify(key)}:${encode(item[key], depth + 1)}`;
    });
    return `{${members.join(',')}}`;
  }
  return Buffer.from(encode(value, 0), 'utf8');
}
