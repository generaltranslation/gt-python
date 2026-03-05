/**
 * Fixture generator for Python static module tests.
 *
 * Imports the actual JS functions from the generaltranslation core package
 * and runs them with a comprehensive input matrix. Writes results to
 * static_fixtures.json.
 *
 * Usage: npx tsx tests/static/fixtures/generate_fixtures.mjs
 */

import { writeFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const GT_CORE =
  "/Users/ernestmccarter/Documents/dev/gt/packages/core/src/static";

const { sanitizeVar } = await import(`${GT_CORE}/utils/sanitizeVar.ts`);
const { declareVar } = await import(`${GT_CORE}/declareVar.ts`);
const { decodeVars } = await import(`${GT_CORE}/decodeVars.ts`);
const { extractVars } = await import(`${GT_CORE}/extractVars.ts`);
const { indexVars } = await import(`${GT_CORE}/indexVars.ts`);
const { condenseVars } = await import(`${GT_CORE}/condenseVars.ts`);

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ---------------------------------------------------------------------------
// sanitize_var
// ---------------------------------------------------------------------------
function generateSanitizeVar() {
  const cases = [];

  function add(label, input) {
    cases.push({ label, input, expected: sanitizeVar(input) });
  }

  // From JS tests
  add("plain text", "Hello World");
  add("braces", "Hello {World}");
  add("quotes", "it's a test");
  add("hash", "item #1");
  add("angle brackets", "<div>hello</div>");
  add("ICU plural", "{count, plural, one {# item} other {# items}}");
  add("variable reference", "Hello {name}!");
  add("date format", "{date, date, short}");
  add("XML tags", "<b>bold</b> and <i>italic</i>");
  add("empty", "");
  add("whitespace", "   ");
  add("consecutive braces", "{{{}}}");
  add("consecutive quotes", "'''");
  add("consecutive brackets", "<<<>>>");
  add("mixed special chars", "{hello} <world> 'test'");
  add("HTML script injection", '<script>alert("xss")</script>');
  add("JSON-like", '{"key": "value", "num": 42}');
  add("price formatting", "$1,234.56");
  add("unicode", "\u00e9\u00e0\u00fc\u00f1");
  add("emojis", "\u{1F600}\u{1F389}\u{1F680}");
  add("chinese with special chars", "\u4f60\u597d {world}");
  add("apostrophes", "it's John's book");
  add("adversarial input", "}{><''{{}}<<>>");

  // Additional edge cases
  add("single char open brace", "{");
  add("single char close brace", "}");
  add("single char lt", "<");
  add("single char gt", ">");
  add("only quotes", "'''");
  add("nested braces", "{{{}}}");
  add("mixed quote types U+0027 and text", "it's here and it's there");
  add("newlines inside braces", "{\nhello\n}");
  add("tab characters", "hello\t{world}");
  add("empty braces", "{}");
  add("opening brace only", "{hello");
  add("closing brace only", "hello}");
  add("angle bracket only", "<hello");
  add("deeply nested", "{a{b{c}d}e}");
  add("special chars at start", "{start");
  add("special chars at end", "end}");
  add("braces and angles mixed", "{a} <b> {c}");
  add("single quote at start", "'hello");
  add("single quote at end", "hello'");
  add("single quote and braces", "it's {here}");
  add("multiple single quotes", "it''s not it'''s");
  add("angle and brace adjacent", "<{test}>");
  add("only angle brackets", "<>");
  add("hash with braces", "# {item}");
  add("complex ICU-like", "{name} bought {count, plural, one {# thing} other {# things}} for <price>{amount}</price>");

  return cases;
}

// ---------------------------------------------------------------------------
// declare_var
// ---------------------------------------------------------------------------
function generateDeclareVar() {
  const cases = [];

  function add(label, variable, options) {
    cases.push({
      label,
      variable,
      options: options || null,
      expected: declareVar(variable, options),
    });
  }

  // From JS tests
  add("undefined", undefined);
  add("null", null);
  add("simple text", "hello");
  add("with name", "hello", { $name: "greeting" });
  add("complex ICU content", "{count, plural, one {# item} other {# items}}");
  add("special chars", "Hello {World} <div>");
  add("quotes with braces", "it's a {test}");

  // Additional edge cases
  add("empty string", "");
  add("boolean true", true);
  add("boolean false", false);
  add("number 0", 0);
  add("number 42", 42);
  add("negative number", -1);
  add("float 3.14", 3.14);
  add("string with newlines", "hello\nworld");
  add("string with tabs", "hello\tworld");
  add("string with unicode", "\u00e9\u00e0\u00fc");
  add("string with emojis", "\u{1F600}\u{1F389}");
  add("string looks like ICU", "{name, select, other {test}}");
  add("name with special chars", "hello", { $name: "var_{name}" });
  add("name with spaces", "hello", { $name: "my variable" });
  add("name with unicode", "hello", { $name: "\u00e9\u00e0" });
  add("name with quotes", "hello", { $name: "it's" });
  add("both special", "{hello}", { $name: "<name>" });

  return cases;
}

// ---------------------------------------------------------------------------
// decode_vars
// ---------------------------------------------------------------------------
function generateDecodeVars() {
  const cases = [];

  function add(label, input) {
    cases.push({ label, input, expected: decodeVars(input) });
  }

  // From JS tests
  add("single var", "{_gt_, select, other {hello}}");
  add("multiple vars", "Hi {_gt_, select, other {Alice}} and {_gt_, select, other {Bob}}");
  add("preserve non-GT elements", "{name} said {_gt_, select, other {hello}}");
  add("empty string", "");
  add("no GT vars", "Hello {name}, you have {count} items");
  add("complex escaped content", "{_gt_, select, other {it''s a ''test''}}");
  add("var at start", "{_gt_, select, other {hello}} world");
  add("var at end", "world {_gt_, select, other {hello}}");
  add("escaped content inside var", "{_gt_, select, other {Hello '{World}'}}");
  add("var with empty content", "{_gt_, select, other {}}");
  add("unicode content", "{_gt_, select, other {\u00e9\u00e0\u00fc}}");
  add("whitespace content", "{_gt_, select, other {   }}");

  // Round-trip with declareVar
  add("round-trip simple", declareVar("Brian"));
  add("round-trip special", declareVar("Hello {World}"));
  add("round-trip quotes", declareVar("it's here"));
  add("round-trip empty", declareVar(""));
  add("round-trip with name", declareVar("hello", { $name: "greeting" }));

  // Adjacent vars
  add("adjacent vars", "{_gt_, select, other {A}}{_gt_, select, other {B}}");
  add("var at very start", "{_gt_, select, other {X}}");
  add("just one var", "{_gt_, select, other {value}}");

  // _gt_ text outside select (should be preserved)
  add("gt text not in select", "The _gt_ prefix is used");
  add("gt in URL", "https://example.com/_gt_/path");

  // Escaped content cases
  add("var with doubled quotes", "{_gt_, select, other {user''s}}");
  add("var with escaped braces", "{_gt_, select, other {'{data}'}}");

  return cases;
}

// ---------------------------------------------------------------------------
// extract_vars
// ---------------------------------------------------------------------------
function generateExtractVars() {
  const cases = [];

  function add(label, input) {
    cases.push({ label, input, expected: extractVars(input) });
  }

  // From JS tests
  add("single var", "{_gt_, select, other {hello}}");
  add("multiple vars", "{_gt_, select, other {alice}} and {_gt_, select, other {bob}}");
  add("no vars", "Hello {name}!");
  add("empty string", "");
  add("special chars", "{_gt_, select, other {Hello '{World}'}}");
  add("unicode", "{_gt_, select, other {\u00e9\u00e0\u00fc}}");
  add("empty other content", "{_gt_, select, other {}}");
  add("mixed with non-GT", "{name} and {_gt_, select, other {test}}");

  // Indexed _gt_1 should be ignored (only unindexed _gt_)
  add("indexed ignored", "{_gt_1, select, other {hello}}");
  add("mixed indexed and unindexed", "{_gt_1, select, other {hello}} and {_gt_, select, other {world}}");

  // Many vars
  add(
    "many vars sequential",
    "{_gt_, select, other {a}} {_gt_, select, other {b}} {_gt_, select, other {c}} {_gt_, select, other {d}} {_gt_, select, other {e}}"
  );

  // No GT prefix
  add("no gt prefix", "just plain text");
  add("gt text not select", "the _gt_ marker");

  // Round-trips
  add("round-trip", declareVar("hello") + " " + declareVar("world"));

  return cases;
}

// ---------------------------------------------------------------------------
// index_vars
// ---------------------------------------------------------------------------
function generateIndexVars() {
  const cases = [];

  function add(label, input) {
    cases.push({ label, input, expected: indexVars(input) });
  }

  // From JS tests
  add("single placeholder", "{_gt_, select, other {hello}}");
  add("multiple placeholders", "{_gt_, select, other {hello}} {_gt_, select, other {world}}");
  add("at start", "{_gt_, select, other {hello}} world");
  add("at end", "world {_gt_, select, other {hello}}");
  add("preserve non-GT", "{name} said {_gt_, select, other {hello}}");
  add("empty string", "");
  add("no GT vars", "Hello {name}!");
  add("var with empty other", "{_gt_, select, other {}}");

  // With _gt_var_name
  add("with var name", "{_gt_, select, other {hello} _gt_var_name {greeting}}");
  add("multiple with var names",
    "{_gt_, select, other {a} _gt_var_name {x}} and {_gt_, select, other {b} _gt_var_name {y}}"
  );

  // GT text outside select
  add("gt text not in select", "The _gt_ prefix is used");
  add("gt in URL", "https://example.com/_gt_/path");

  // Adjacent vars
  add("adjacent vars", "{_gt_, select, other {A}}{_gt_, select, other {B}}");

  // Round-trips
  add("round-trip simple", declareVar("hello"));
  add("round-trip with name", declareVar("hello", { $name: "greeting" }));
  add("round-trip special", declareVar("Hello {World}"));

  // Complex: vars mixed with other ICU
  add("mixed with plain var", "{name} {_gt_, select, other {val}}");

  // Many vars
  add(
    "many sequential",
    "{_gt_, select, other {a}} {_gt_, select, other {b}} {_gt_, select, other {c}} {_gt_, select, other {d}} {_gt_, select, other {e}}"
  );

  // Escaped content in other
  add("escaped in other", "{_gt_, select, other {it''s here}}");
  add("escaped braces in other", "{_gt_, select, other {'{braces}'}}");

  // Verify output is valid ICU
  for (const c of cases) {
    if (c.expected && c.expected.includes("_gt_")) {
      try {
        // Just verify it doesn't throw
        indexVars(c.input);
      } catch (e) {
        console.warn(`Warning: indexVars threw for ${c.label}: ${e.message}`);
      }
    }
  }

  return cases;
}

// ---------------------------------------------------------------------------
// condense_vars
// ---------------------------------------------------------------------------
function generateCondenseVars() {
  const cases = [];

  function add(label, input) {
    cases.push({ label, input, expected: condenseVars(input) });
  }

  // From JS tests
  add("basic single", "{_gt_1, select, other {hello}}");
  add("basic multiple", "{_gt_1, select, other {hello}} {_gt_2, select, other {world}}");
  add("preserve non-indexed selects", "{gender, select, male {He} female {She} other {They}}");
  add("plain text", "Hello World");
  add("non-select vars", "{name} and {count}");
  add("empty string", "");
  add("mixed indexed and regular args", "{_gt_1, select, other {hello}} {name}");
  add("single digit index", "{_gt_1, select, other {x}}");
  add("multi digit index", "{_gt_10, select, other {x}}");
  add("zero index", "{_gt_0, select, other {x}}");

  // Invalid patterns
  add("no prefix", "{foo, select, other {bar}}");
  add("non-numeric suffix", "{_gt_abc, select, other {bar}}");
  add("extra chars after num", "{_gt_1abc, select, other {bar}}");

  // Additional edge cases
  add("large index", "{_gt_9999, select, other {x}}");
  add("consecutive indexed 1-5",
    "{_gt_1, select, other {a}} {_gt_2, select, other {b}} {_gt_3, select, other {c}} {_gt_4, select, other {d}} {_gt_5, select, other {e}}"
  );
  add("indexed with var_name", "{_gt_1, select, other {hello} _gt_var_name {greeting}}");
  add("empty other", "{_gt_1, select, other {}}");
  add("back-to-back no text", "{_gt_1, select, other {a}}{_gt_2, select, other {b}}");
  add("mix condensable and non", "{_gt_1, select, other {hello}} {gender, select, male {He} other {They}}");
  add("whitespace around indexed", "  {_gt_1, select, other {hello}}  ");
  add("text before and after", "Hello {_gt_1, select, other {name}} goodbye");

  // Unindexed should NOT be condensed
  add("unindexed not condensed", "{_gt_, select, other {hello}}");

  // Escaped content
  add("escaped quotes in other", "{_gt_1, select, other {user''s data}}");
  add("escaped braces in other", "{_gt_1, select, other {'{data}'}}");

  // String with only GT identifier text
  add("gt text not select", "The _gt_ prefix");
  add("gt in url", "https://example.com/_gt_1/path");

  // Round-trip: declareVar → indexVars → condenseVars
  const roundTrip1 = indexVars(declareVar("hello"));
  add("round-trip simple", roundTrip1);
  const roundTrip2 = indexVars(declareVar("Hello {World}"));
  add("round-trip special", roundTrip2);
  const roundTrip3 = indexVars(
    declareVar("hello", { $name: "greeting" })
  );
  add("round-trip with name", roundTrip3);
  const roundTrip4 = indexVars(
    declareVar("a") + " and " + declareVar("b")
  );
  add("round-trip multiple", roundTrip4);

  return cases;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const fixtures = {
  sanitize_var: generateSanitizeVar(),
  declare_var: generateDeclareVar(),
  decode_vars: generateDecodeVars(),
  extract_vars: generateExtractVars(),
  index_vars: generateIndexVars(),
  condense_vars: generateCondenseVars(),
};

const outputPath = join(__dirname, "static_fixtures.json");
writeFileSync(outputPath, JSON.stringify(fixtures, null, 2) + "\n");
console.log(`Wrote ${outputPath}`);
for (const [key, val] of Object.entries(fixtures)) {
  console.log(`  ${key}: ${val.length} cases`);
}
