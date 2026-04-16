/**
 * Generate bulk parity fixtures for the runtime-translation port.
 *
 * Exercises hashMessage (the JS ``hashSource`` with indexVars for ICU only)
 * across a wide combinatorial space of (message, format, context, id, maxChars).
 *
 * Run:
 *   cd ~/Documents/dev/gt && \
 *     node ~/Documents/dev/gt-python-wt/e-i18n-add-runtime-translation/packages/gt-i18n/tests/fixtures/generate_runtime_fixtures.mjs \
 *     > ~/Documents/dev/gt-python-wt/e-i18n-add-runtime-translation/packages/gt-i18n/tests/fixtures/runtime_translation_parity.json
 */

import { hashSource } from 'generaltranslation/id';
import { indexVars } from 'generaltranslation/internal';

// ---------------------------------------------------------------------------
// Message corpora per format
// ---------------------------------------------------------------------------

const ICU_MESSAGES = [
  "",
  "Hello",
  "Hello, world!",
  "Hello, {name}!",
  "{count, plural, one {# item} other {# items}}",
  "{count, plural, one {# item} other {# items}} in cart",
  "{gender, select, male {he} female {she} other {they}}",
  "Hello {name} ({email})",
  "Welcome to {app}, {user}!",
  "{_gt_, select, other {John}}",
  "Hello {_gt_, select, other {John}}!",
  "Hello {_gt_, select, other {John}} and {_gt_, select, other {Jane}}",
  "Hello {_gt_, select, other {John} _gt_var_name {user}}!",
  "Save",
  "Cancel",
  "Delete {count, plural, one {# item} other {# items}}",
  "Você tem {count, plural, one {# mensagem} other {# mensagens}}",
  "こんにちは、{name}さん！",
  "🎉 Welcome, {name}! 🎉",
  "{a}{b}{c}{d}{e}",
  "   leading and trailing whitespace   ",
  "Line1\nLine2\nLine3",
  "Tab\there",
  "A very long message that goes on and on and on and on and repeats many words many times in sequence for testing long-content handling behavior within the hash computation pipeline end-to-end.",
];

const STRING_MESSAGES = [
  "",
  "Hello",
  "Hello, world!",
  "Hello, {name}!",
  "Welcome {user}!",
  "Items: {count}",
  "   whitespace   ",
  "Line1\nLine2",
  "emoji 🎉 test",
  "こんにちは",
  "Long" + " string".repeat(50),
  "{}",
  "{{escaped}}",
  "{a}{b}{c}",
  "single_word",
  "hyphen-ated",
  "under_scored",
];

const I18NEXT_MESSAGES = [
  "",
  "Hello",
  "Hello, world!",
  "Hello, {{name}}!",
  "Welcome {{user}}!",
  "You have {{count}} items",
  "Nested {{outer}} with {{inner}}",
  "Mixed {{name}} and {count}",
  "   whitespace   ",
  "emoji 🎉 {{name}}",
  "{{a}}{{b}}{{c}}",
];

// ---------------------------------------------------------------------------
// Option variants
// ---------------------------------------------------------------------------

const CONTEXTS = [null, "", "button", "menu", "a_very_long_context_value_for_testing", "こんにちは"];
const IDS = [null, "", "greeting", "user.profile.button", "x/y/z", "a-b-c"];
const MAX_CHARS_VALUES = [null, 0, 5, 50, 1000, -10, -500];

// ---------------------------------------------------------------------------
// Generate
// ---------------------------------------------------------------------------

function hashMessage(message, format, options) {
  return hashSource({
    source: format === "ICU" ? indexVars(message) : message,
    ...(options.context && { context: options.context }),
    ...(options.id && { id: options.id }),
    ...(options.maxChars != null && { maxChars: Math.abs(options.maxChars) }),
    dataFormat: format,
  });
}

const cases = [];

function addCases(format, messages) {
  // Full matrix for each message: basic, each context, each id, each maxChars.
  for (const message of messages) {
    // Plain (no options)
    cases.push({ message, format, context: null, id: null, maxChars: null });
    // Each context
    for (const context of CONTEXTS.filter((c) => c !== null)) {
      cases.push({ message, format, context, id: null, maxChars: null });
    }
    // Each id
    for (const id of IDS.filter((i) => i !== null)) {
      cases.push({ message, format, context: null, id, maxChars: null });
    }
    // Each maxChars
    for (const maxChars of MAX_CHARS_VALUES.filter((m) => m !== null)) {
      cases.push({ message, format, context: null, id: null, maxChars });
    }
    // Context + id together (sample)
    cases.push({ message, format, context: "button", id: "save_btn", maxChars: null });
    // Context + maxChars together (sample)
    cases.push({ message, format, context: "menu", id: null, maxChars: 20 });
    // All three
    cases.push({ message, format, context: "menu", id: "menu_save", maxChars: 50 });
  }
}

addCases("ICU", ICU_MESSAGES);
addCases("STRING", STRING_MESSAGES);
addCases("I18NEXT", I18NEXT_MESSAGES);

// Compute hashes
for (const c of cases) {
  c.hash = hashMessage(c.message, c.format, {
    context: c.context,
    id: c.id,
    maxChars: c.maxChars,
  });
}

// Also emit a few cross-format collision checks: same (message, context, id, maxChars)
// across ICU vs STRING vs I18NEXT should produce DIFFERENT hashes.
const collisionCases = [];
for (const message of ["", "Hello", "Hello, {name}!", "simple"]) {
  for (const context of [null, "button"]) {
    const setOfHashes = {};
    for (const format of ["ICU", "STRING", "I18NEXT"]) {
      setOfHashes[format] = hashMessage(message, format, {
        context,
        id: null,
        maxChars: null,
      });
    }
    collisionCases.push({ message, context, hashes: setOfHashes });
  }
}

const output = {
  note: "Generated by generate_runtime_fixtures.mjs. Do not edit by hand.",
  caseCount: cases.length,
  cases,
  collisionCases,
};

// Stdout — redirect to fixture JSON file.
process.stdout.write(JSON.stringify(output, null, 2));
