/**
 * Generate test fixtures from the JS supported-locales package.
 * Run: node packages/supported-locales/tests/fixtures/generate_fixtures.mjs
 */

// Use absolute path to the JS dist in the gt monorepo
const GT_JS_ROOT = process.env.GT_JS_ROOT || '/Users/ernestmccarter/Documents/dev/gt';
const { getSupportedLocale, listSupportedLocales } = await import(
  `${GT_JS_ROOT}/packages/supported-locales/dist/index.esm.min.mjs`
);
import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Get the full supported locales list for exhaustive testing
const allLocales = listSupportedLocales();

// Build get_supported_locale test cases
const getSupportedLocaleCases = [];

// 1. Every exact locale in the supported list
for (const locale of allLocales) {
  getSupportedLocaleCases.push({
    input: locale,
    expected: getSupportedLocale(locale),
  });
}

// 2. Invalid inputs
const invalidInputs = ["", "not-a-locale", "123", "xx"];
for (const input of invalidInputs) {
  getSupportedLocaleCases.push({
    input,
    expected: getSupportedLocale(input),
  });
}

// 3. Case variations
const caseVariations = ["en-us", "EN-US", "ZH-HANS-CN"];
for (const input of caseVariations) {
  getSupportedLocaleCases.push({
    input,
    expected: getSupportedLocale(input),
  });
}

// 4. Locales with redundant scripts
const redundantScripts = ["en-Latn-US", "fr-Latn-FR", "zh-Hans-CN"];
for (const input of redundantScripts) {
  getSupportedLocaleCases.push({
    input,
    expected: getSupportedLocale(input),
  });
}

// 5. Unsupported regions that should fall back
const fallbackRegions = ["de-LU", "fr-DZ", "en-IE", "es-BO"];
for (const input of fallbackRegions) {
  getSupportedLocaleCases.push({
    input,
    expected: getSupportedLocale(input),
  });
}

// 6. Unsupported languages
const unsupportedLangs = ["zu", "xh", "wo"];
for (const input of unsupportedLangs) {
  getSupportedLocaleCases.push({
    input,
    expected: getSupportedLocale(input),
  });
}

// 7. Private-use/experimental
getSupportedLocaleCases.push({
  input: "qbr",
  expected: getSupportedLocale("qbr"),
});

// 8. Script variants
const scriptVariants = ["zh-Hant-TW", "zh-Hant-HK"];
for (const input of scriptVariants) {
  getSupportedLocaleCases.push({
    input,
    expected: getSupportedLocale(input),
  });
}

// Build output
const fixtures = {
  get_supported_locale: getSupportedLocaleCases,
  list_supported_locales: {
    expected: allLocales,
  },
};

const outPath = join(__dirname, 'supported_locales_fixtures.json');
writeFileSync(outPath, JSON.stringify(fixtures, null, 2) + '\n');
console.log(`Wrote ${getSupportedLocaleCases.length} get_supported_locale cases`);
console.log(`Wrote ${allLocales.length} list_supported_locales entries`);
console.log(`Output: ${outPath}`);
