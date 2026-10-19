import { canonicalBytes } from './strict-json.mjs';
import { isIP } from 'node:net';

export const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export const isString = value => typeof value === 'string' && [...value].length > 0;

export function absoluteUri(value) {
  if (typeof value !== 'string'
    || !/^[A-Za-z][A-Za-z0-9+.-]*:[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$/.test(value)
    || /%(?![0-9A-Fa-f]{2})/.test(value)) return false;
  // RFC 3986 Appendix A, not WHATWG URL normalization or dereferencing.
  const fragments = value.slice(value.indexOf(':') + 1).split('#');
  if (fragments.length > 2) return false;
  const queryAt = fragments[0].indexOf('?');
  let path = queryAt < 0 ? fragments[0] : fragments[0].slice(0, queryAt);
  const query = queryAt < 0 ? '' : fragments[0].slice(queryAt + 1);
  const queryOrFragment = /^[A-Za-z0-9._~!$&'()*+,;=%:@\/?-]*$/;
  if (!queryOrFragment.test(query) || !queryOrFragment.test(fragments[1] ?? '')) return false;
  if (path.startsWith('//')) {
    const slash = path.indexOf('/', 2);
    const authority = slash < 0 ? path.slice(2) : path.slice(2, slash);
    path = slash < 0 ? '' : path.slice(slash);
    const at = authority.split('@');
    if (at.length > 2 || (at.length === 2 && !/^[A-Za-z0-9._~!$&'()*+,;=%:-]*$/.test(at[0]))) return false;
    const hostPort = at.at(-1);
    if (hostPort.startsWith('[')) {
      const close = hostPort.indexOf(']');
      if (close < 0 || !/^(?::[0-9]*)?$/.test(hostPort.slice(close + 1))) return false;
      const literal = hostPort.slice(1, close);
      const future = /^v[0-9a-f]+\.[A-Za-z0-9._~!$&'()*+,;=:-]+$/i.test(literal);
      if (!future && (literal.includes('%') || isIP(literal) !== 6)) return false;
    } else {
      const parts = hostPort.split(':');
      if (parts.length > 2 || !/^[A-Za-z0-9._~!$&'()*+,;=%-]*$/.test(parts[0])
        || (parts.length === 2 && !/^[0-9]*$/.test(parts[1]))) return false;
    }
  }
  return /^[A-Za-z0-9._~!$&'()*+,;=%:@\/-]*$/.test(path);
}

// Only the vocabulary used by the trusted, bundled schema is implemented.
export function compileBundledSchema(root) {
  const supported = new Set(['$schema', '$id', 'title', 'description', '$defs', '$ref',
    'type', 'properties', 'required', 'additionalProperties', 'propertyNames',
    'minProperties', 'maxProperties', 'items', 'minItems', 'maxItems', 'uniqueItems',
    'minLength', 'maxLength', 'pattern', 'format', 'enum', 'const',
    'allOf', 'oneOf', 'anyOf', 'if', 'then', 'else', 'not']);
  function inspect(schema) {
    if (!isObject(schema)) throw new Error('Unsupported bundled schema');
    if (Object.keys(schema).some(key => !supported.has(key))) throw new Error('Unsupported schema keyword');
    if (schema.format && schema.format !== 'uri') throw new Error('Unsupported schema format');
    if (schema.type && !['object', 'array', 'string', 'integer', 'number', 'boolean', 'null'].includes(schema.type)) {
      throw new Error('Unsupported schema type');
    }
    if (schema.$ref && !/^#\/\$defs\/[^/]+$/.test(schema.$ref)) throw new Error('Nonlocal schema reference');
    for (const key of ['properties', '$defs']) for (const child of Object.values(schema[key] ?? {})) inspect(child);
    for (const key of ['items', 'propertyNames', 'if', 'then', 'else', 'not']) if (schema[key]) inspect(schema[key]);
    for (const key of ['allOf', 'oneOf', 'anyOf']) for (const child of schema[key] ?? []) inspect(child);
  }
  inspect(root);
  function validate(schema, value) {
    if (schema.$ref && !validate(root.$defs[schema.$ref.slice(8)], value)) return false;
    if (Object.hasOwn(schema, 'const') && value !== schema.const) return false;
    if (schema.enum && !schema.enum.includes(value)) return false;
    const types = {
      object: isObject, array: Array.isArray, string: v => typeof v === 'string',
      integer: Number.isSafeInteger, number: v => typeof v === 'number' && Number.isFinite(v),
      boolean: v => typeof v === 'boolean', null: v => v === null
    };
    if (schema.type && !types[schema.type](value)) return false;
    if (schema.allOf && !schema.allOf.every(child => validate(child, value))) return false;
    if (schema.oneOf && schema.oneOf.filter(child => validate(child, value)).length !== 1) return false;
    if (schema.anyOf && !schema.anyOf.some(child => validate(child, value))) return false;
    if (schema.not && validate(schema.not, value)) return false;
    if (schema.if) {
      const branch = validate(schema.if, value) ? schema.then : schema.else;
      if (branch && !validate(branch, value)) return false;
    }
    if (typeof value === 'string') {
      const length = [...value].length;
      if (length < (schema.minLength ?? 0) || length > (schema.maxLength ?? Infinity)) return false;
      if (schema.pattern && !new RegExp(schema.pattern).test(value)) return false;
      if (schema.format === 'uri' && !absoluteUri(value)) return false;
    }
    if (Array.isArray(value)) {
      if (value.length < (schema.minItems ?? 0) || value.length > (schema.maxItems ?? Infinity)) return false;
      if (schema.uniqueItems && new Set(value.map(v => canonicalBytes(v).toString())).size !== value.length) return false;
      if (schema.items && !value.every(child => validate(schema.items, child))) return false;
    }
    if (isObject(value)) {
      const keys = Object.keys(value);
      if (keys.length < (schema.minProperties ?? 0) || keys.length > (schema.maxProperties ?? Infinity)) return false;
      if (schema.required?.some(key => !Object.hasOwn(value, key))) return false;
      if (schema.additionalProperties === false && keys.some(key => !Object.hasOwn(schema.properties ?? {}, key))) return false;
      if (schema.propertyNames && keys.some(key => !validate(schema.propertyNames, key))) return false;
      for (const [key, child] of Object.entries(schema.properties ?? {})) {
        if (Object.hasOwn(value, key) && !validate(child, value[key])) return false;
      }
    }
    return true;
  }
  return value => validate(root, value);
}
