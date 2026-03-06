import { createHash } from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Reimplement fast-json-stable-stringify: sorts keys alphabetically, no spaces
function stableStringify(obj) {
  if (obj === null || obj === undefined) return JSON.stringify(obj);
  if (typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) {
    return '[' + obj.map(item => stableStringify(item)).join(',') + ']';
  }
  const keys = Object.keys(obj).sort();
  const parts = keys.map(key => JSON.stringify(key) + ':' + stableStringify(obj[key]));
  return '{' + parts.join(',') + '}';
}

// Matches CryptoJS.SHA256(string).toString(CryptoJS.enc.Hex).slice(0, 16)
function hashString(string) {
  return createHash('sha256').update(string).digest('hex').slice(0, 16);
}

function hashSource({ source, context, id, maxChars, dataFormat }) {
  let sanitizedData = { dataFormat };
  // Non-JSX path: source is used as-is
  sanitizedData.source = source;

  sanitizedData = {
    ...sanitizedData,
    ...(id && { id }),
    ...(context && { context }),
    ...(maxChars != null && { maxChars: Math.abs(maxChars) }),
  };
  const stringifiedData = stableStringify(sanitizedData);
  return hashString(stringifiedData);
}

function hashTemplate(template) {
  return hashString(stableStringify(template));
}

const fixtures = {
  hash_string: [],
  hash_source: [],
  hash_template: [],
};

// hash_string test cases
const strings = ["", "hello", "Hello, world!", "test 123", "unicode: 你好世界", "special chars: !@#$%^&*()"];
for (const s of strings) {
  fixtures.hash_string.push({ input: s, expected: hashString(s) });
}

// hash_source test cases (only ICU/STRING, no JSX)
const sources = [
  { source: "Hello", dataFormat: "ICU" },
  { source: "Hello", dataFormat: "STRING" },
  { source: "Hello", context: "greeting", dataFormat: "ICU" },
  { source: "Hello", id: "greeting-id", dataFormat: "ICU" },
  { source: "Hello", maxChars: 100, dataFormat: "ICU" },
  { source: "Hello", maxChars: -50, dataFormat: "ICU" },
  { source: "Hello", context: "ctx", id: "my-id", maxChars: 200, dataFormat: "ICU" },
  { source: "", dataFormat: "ICU" },
  { source: "A longer message with {variables}", dataFormat: "ICU" },
  { source: "Test", dataFormat: "I18NEXT" },
];

for (const s of sources) {
  fixtures.hash_source.push({
    input: s,
    expected: hashSource(s),
  });
}

// hash_template test cases
const templates = [
  { key1: "value1" },
  { a: "1", b: "2" },
  { z: "last", a: "first" },
  {},
  { hello: "world", foo: "bar" },
];

for (const t of templates) {
  fixtures.hash_template.push({
    input: t,
    expected: hashTemplate(t),
  });
}

fs.writeFileSync(
  path.join(__dirname, 'id_fixtures.json'),
  JSON.stringify(fixtures, null, 2)
);

console.log(`Generated ${fixtures.hash_string.length + fixtures.hash_source.length + fixtures.hash_template.length} test cases`);
