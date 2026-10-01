/**
 * Wording lint for this plugin (`make copy`, part of `make check`): README, skills and the human-facing strings of
 * .claude-plugin/plugin.json must not use the words in copy-rules.json (advice-like, certainty, broker, hype and
 * jargon words). The lists are generated from the DIVID copy rules; do not edit copy-rules.json by hand.
 * Markdown syntax that is not copy (code, URLs, image/link markup, front-matter keys) is removed first; a ```text
 * fence is copy and is linted (PLG-407a P-3: the approved answers live in one).
 * copy-allow.txt holds reviewed exceptions, one per line (`  # reason` after two spaces): an exact substring, or
 * `re:<regex>` for instructions that quote the words they forbid.
 *   node .github/check/copy_lint.mjs <file|dir>...        exit 1 on any hit
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const RULES = JSON.parse(readFileSync(join(here, 'copy-rules.json'), 'utf-8'));
const NEVER = RULES.never;
const ALLOWED = RULES.allowed.map((a) => new RegExp(a.source, a.flags));
const escape = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** Words that must not appear in `text`; the same results as the DIVID app copy lint. */
export function lint(text) {
  let s = text.replace(/\{\w+\}/g, ' ');
  for (const re of ALLOWED) s = s.replace(re, ' ');
  const hits = [];
  for (const w of NEVER) {
    if (new RegExp(`(?<![\\w-])${escape(w)}(?![\\w-])`, 'i').test(s)) hits.push(w);
  }
  if (/\badvice\b/i.test(s)) hits.push('advice (outside "not financial advice")');
  if (s.includes('!')) hits.push('"!"');
  if (/\p{Extended_Pictographic}/u.test(s)) hits.push('emoji');
  return hits;
}

const TEXT = /\.(md|txt|json)$/i;

function walk(p) {
  if (statSync(p).isFile()) return [p];
  return readdirSync(p)
    .filter((n) => !n.startsWith('.git') && n !== 'node_modules')
    .flatMap((n) => walk(join(p, n)))
    .filter((f) => TEXT.test(f) || f.endsWith('/.mcp.json'));
}

/** Only the human-facing strings of a JSON manifest. */
function jsonCopy(text) {
  const j = JSON.parse(text);
  const out = [];
  for (const k of ['description', 'displayName']) if (typeof j[k] === 'string') out.push(j[k]);
  if (Array.isArray(j.keywords)) out.push(...j.keywords);
  return out;
}

function markdownCopy(text) {
  const body = text
    .replace(/^---\n[\s\S]*?\n---\n/, (fm) => fm.replace(/^\s*[\w-]+:\s*/gm, '')) // keep front-matter values only
    .replace(/^(```|~~~)text[ \t]*\n([\s\S]*?)^\1[ \t]*$/gm, '$2') // a `text` fence is copy (approved answers, 18 §2.3 P-3)
    .replace(/(```|~~~)[\s\S]*?\1/g, ' ') // fenced code
    .replace(/`[^`\n]*`/g, ' ') // inline code
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1') // images: alt text is copy
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1') // links: label is copy
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/https?:\/\/\S+/g, ' ');
  return body.split(/\n{2,}/); // paragraphs, so a hit names its context
}

function main(args) {
  if (!args.length) {
    console.error('usage: node .github/check/copy_lint.mjs <file|dir>...');
    return 2;
  }
  const allow = readFileSync(join(here, 'copy-allow.txt'), 'utf-8')
    .split('\n')
    .filter((l) => l.trim() && !l.startsWith('#'))
    .map((l) => l.replace(/\s{2,}#.*$/, ''));
  const used = new Set();
  const unallowed = (text) => {
    let s = text;
    for (const a of allow) {
      if (a.startsWith('re:')) {
        const re = new RegExp(a.slice(3), 'g');
        if (re.test(s)) {
          used.add(a);
          s = s.replace(re, ' ');
        }
      } else if (s.includes(a)) {
        used.add(a);
        s = s.split(a).join(' ');
      }
    }
    return s;
  };
  let hits = 0;
  let files = 0;
  for (const root of args) {
    for (const file of walk(root)) {
      const text = unallowed(readFileSync(file, 'utf-8'));
      const name = relative(process.cwd(), file) || file;
      let parts;
      if (file.endsWith('.json')) {
        if (!/plugin\.json$/.test(file)) continue; // other JSON (.mcp.json) carries no copy
        parts = jsonCopy(text);
      } else parts = markdownCopy(text);
      files += 1;
      for (const part of parts) {
        const found = lint(part);
        if (found.length) {
          hits += found.length;
          console.log(`FAIL  ${name}: ${found.join(', ')} in "${part.trim().replace(/\s+/g, ' ').slice(0, 120)}"`);
        }
      }
    }
  }
  for (const a of allow) if (!used.has(a)) console.log(`note  allow-list entry not used (remove it?): ${a}`);
  console.log(`copy lint: ${files} file(s), ${hits} hit(s), ${used.size} allow-list exception(s) applied`);
  return hits ? 1 : 0;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) process.exit(main(process.argv.slice(2)));
