/**
 * Generate test fixtures by running JS hashMessage + indexVars.
 * Run: node packages/gt-i18n/tests/fixtures/generate_fixtures.mjs
 */

import { hashSource, hashString } from 'generaltranslation/id';
import { indexVars } from 'generaltranslation/internal';

// Test cases for indexVars
const indexVarsCases = [
  { input: "Hello, world!", label: "plain_no_vars" },
  { input: "Hello, {name}!", label: "simple_variable" },
  { input: "{_gt_, select, other {Hello World}}", label: "single_gt" },
  { input: "Hello {_gt_, select, other {John}} and {_gt_, select, other {Jane}}", label: "two_gt" },
  { input: "Hello {_gt_, select, other {John} _gt_var_name {John}} and {_gt_, select, other {Jane}}", label: "gt_with_var_name" },
  { input: "{count, plural, one {{_gt_, select, other {item}}} other {{_gt_, select, other {items}}}}", label: "nested_in_plural" },
  { input: "", label: "empty_string" },
  { input: "No placeholders here", label: "no_placeholders" },
];

console.log("=== indexVars ===");
const indexVarsResults = {};
for (const c of indexVarsCases) {
  const result = indexVars(c.input);
  indexVarsResults[c.label] = { input: c.input, output: result };
  console.log(`${c.label}: ${JSON.stringify(c.input)} => ${JSON.stringify(result)}`);
}

// Test cases for hashMessage (= hashSource(indexVars(msg), dataFormat: "ICU"))
console.log("\n=== hashMessage ===");

function hashMessage(message, options = {}) {
  return hashSource({
    source: indexVars(message),
    ...(options.context && { context: options.context }),
    ...(options.id && { id: options.id }),
    ...(options.maxChars != null && { maxChars: Math.abs(options.maxChars) }),
    dataFormat: "ICU",
  });
}

const hashCases = [
  { message: "Hello, world!", options: {}, label: "plain" },
  { message: "Hello, {name}!", options: {}, label: "with_variable" },
  { message: "Save", options: { context: "button" }, label: "with_context_button" },
  { message: "Save", options: { context: "menu" }, label: "with_context_menu" },
  { message: "Save", options: {}, label: "no_context" },
  { message: "Hello", options: { id: "greeting" }, label: "with_id" },
  { message: "Hello", options: { maxChars: 10 }, label: "with_max_chars" },
  { message: "Hello", options: { maxChars: -10 }, label: "with_negative_max_chars" },
  { message: "", options: {}, label: "empty" },
  { message: "{count, plural, one {# item} other {# items}}", options: {}, label: "plural" },
  { message: "You have {count, plural, one {# item} other {# items}}.", options: {}, label: "plural_sentence" },
  { message: "Hello {_gt_, select, other {John}}!", options: {}, label: "with_gt_var" },
  { message: "Hello {_gt_, select, other {John} _gt_var_name {user}}!", options: {}, label: "with_gt_var_name" },
  { message: "Save", options: { context: "button", id: "save_btn" }, label: "context_and_id" },
  { message: "Save", options: { context: "button", maxChars: 20 }, label: "context_and_max_chars" },
];

const hashResults = {};
for (const c of hashCases) {
  const hash = hashMessage(c.message, c.options);
  hashResults[c.label] = { message: c.message, options: c.options, hash };
  console.log(`${c.label}: hashMessage(${JSON.stringify(c.message)}, ${JSON.stringify(c.options)}) => ${JSON.stringify(hash)}`);
}

// Also test the intermediate: what does stringify produce?
console.log("\n=== stringify debug ===");
import stringify from 'fast-json-stable-stringify';
const debugCases = [
  { source: "Hello, world!", dataFormat: "ICU" },
  { source: "Hello, world!", dataFormat: "ICU", context: "button" },
  { source: "Hello, world!", dataFormat: "ICU", id: "greeting" },
  { source: "Hello, world!", dataFormat: "ICU", maxChars: 10 },
];
for (const c of debugCases) {
  console.log(`stringify(${JSON.stringify(c)}) => ${stringify(c)}`);
  console.log(`hashString => ${hashString(stringify(c))}`);
}

// Output as JSON for easy Python consumption
console.log("\n=== JSON FIXTURES ===");
console.log(JSON.stringify({ indexVars: indexVarsResults, hashMessage: hashResults }, null, 2));
