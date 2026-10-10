#!/usr/bin/env python3
"""File rules for this plugin (`make files`, part of `make check` and of .github/workflows/validate.yml).

Usage: python3 .github/check/check_bundle.py .

Covers the automated rows of the pre-submission checklist that `claude plugin validate` does not
(https://claude.com/docs/plugins/pre-submission-checklist): layout, names, sizes, file types, what the plugin runs,
the remote MCP entry, the manifest, the README and the skills. Repository tooling (`.github/`, `Makefile`) follows
the same name, size, type and secret rules; only the host and wording rules for plugin content skip it.
Standard library only (PyYAML is used for skill front matter when installed). Exit code 1 on any failure.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

KIB = 1024
MIB = 1024 * KIB
SYSTEM_FILES = {'.ds_store', 'thumbs.db', 'desktop.ini', '__macosx'}
WIN_DEVICES = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
FONT_EXT = {'.woff', '.woff2', '.ttf', '.otf'}
PKG_CONFIGS = {'.npmrc', 'bunfig.toml', 'uv.toml', '.yarnrc', '.yarnrc.yml', 'pip.conf'}
LOCKFILES = {'package-lock.json', 'npm-shrinkwrap.json', 'bun.lock', 'bun.lockb'}
LAUNCHERS = re.compile(r'\b(npx|bunx|pnpm dlx|yarn dlx|uvx|pipx run|uv run)\b')
ALLOWED_HOSTS = {'divid.ai', 'mcp.divid.ai', 'auth.divid.ai'}
MCP_URL = 'https://mcp.divid.ai/mcp'
# Server key = plugin slug (Director decision 2026-10-01): tools appear as mcp__divid-planner__*.
MCP_KEY = 'divid-planner'
SECRET_PATTERNS = [
    re.compile(p)
    for p in (
        r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
        r'\bAKIA[0-9A-Z]{16}\b',
        r'\bgh[pousr]_[A-Za-z0-9]{30,}\b',
        r'\bxox[abpr]-[A-Za-z0-9-]{10,}',
        r'\bsk-[A-Za-z0-9_-]{20,}',
        r'\bAIza[0-9A-Za-z_-]{35}\b',
        r'(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*["\']?[A-Za-z0-9_\-+/]{12,}',
        r'(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._-]{12,}',
        r'\d{8,10}:[A-Za-z0-9_-]{35}',  # Telegram bot token
    )
]
INTERNAL_HINTS = re.compile(r'(?i)\b(divid\.team|localhost|127\.0\.0\.1|api-planner|api-auth|invest_bot|next-generation)\b')
D14 = 'DIVID Planner is a self-directed planning and simulation tool, not a financial adviser.'
D15 = 'The plugin connects to one remote server, `https://mcp.divid.ai/mcp`, operated by DIVID AI TECH LLC.'
BANNED_KEYWORDS = re.compile(r'(?i)advice|advisor|adviser|retirement')
LISTING_URLS = ('documentationUrl', 'supportUrl', 'privacyPolicyUrl', 'termsOfServiceUrl')
# DIVID rule D28: no directory or listing words in the README or the manifest until the plugin is listed (drop this rule
# with the first release after the listing goes live). HTML comments are skipped; release_check.py guards those.
NOT_LISTED_YET = re.compile(r'(?i)\b(director(y|ies)|marketplaces?|listed|listings?)\b')


def is_tooling(rel: Path) -> bool:
    """Repository tooling, not plugin content: exempt from the public-host and internal-name rules only."""
    s = rel.as_posix()
    return s == 'Makefile' or s.startswith('.github/')


failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


_mark = [0]


def ok(msg: str) -> None:
    """Record a passed section, only if it added no failure since the previous ok()."""
    if len(failures) == _mark[0]:
        notes.append(msg)
    _mark[0] = len(failures)


def files_of(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob('*') if '.git' not in p.relative_to(root).parts[:1])


def is_complete_image(p: Path, data: bytes) -> bool:
    ext = p.suffix.lower()
    if ext == '.png':
        return data.startswith(b'\x89PNG\r\n\x1a\n') and data.endswith(b'IEND\xaeB`\x82')
    if ext in {'.jpg', '.jpeg'}:
        return data.startswith(b'\xff\xd8') and data.rstrip(b'\x00').endswith(b'\xff\xd9')
    if ext == '.gif':
        return data[:6] in (b'GIF87a', b'GIF89a') and data.endswith(b';')
    if ext == '.webp':
        return data[:4] == b'RIFF' and data[8:12] == b'WEBP' and int.from_bytes(data[4:8], 'little') + 8 == len(data)
    if ext == '.svg':
        return b'<svg' in data[:4096]
    return False


def readme_words(text: str) -> int:
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
            continue
        if not fenced:
            out.append(re.sub(r'`[^`]*`', ' ', line))  # inline code does not count either (conservative)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.,&-]*", ' '.join(out)))


def check(root: Path) -> None:
    paths = files_of(root)
    files = [p for p in paths if p.is_file() or p.is_symlink()]
    rel = [p.relative_to(root) for p in paths]

    # B1/B2/B10: layout
    if not (root / '.claude-plugin' / 'plugin.json').is_file():
        fail('B1 .claude-plugin/plugin.json missing')
    extra = [p.name for p in (root / '.claude-plugin').iterdir()] if (root / '.claude-plugin').is_dir() else []
    if extra != ['plugin.json']:
        fail(f'B1 only plugin.json may live in .claude-plugin/, found {extra}')
    if (root / 'bin').exists():
        fail('B10 top-level bin/ present (claude.ai and Cowork refuse to install)')
    # B4: symlinks, submodules, LFS
    for p in paths:
        if p.is_symlink():
            fail(f'B4 symlink: {p.relative_to(root)}')
    try:
        staged = subprocess.run(['git', '-C', str(root), 'ls-files', '-s'], capture_output=True, text=True, check=True)
        bad = [ln for ln in staged.stdout.splitlines() if ln.startswith(('120000', '160000'))]
        if bad:
            fail(f'B4 git modes 120000/160000: {bad}')
        if len(staged.stdout.splitlines()) >= 10_000:
            fail(f'B9 {len(staged.stdout.splitlines())} git entries >= 10,000')
        ok(f'B4 git ls-files -s: {len(staged.stdout.splitlines())} entries, none with mode 120000/160000')
    except (subprocess.CalledProcessError, FileNotFoundError):
        notes.append('B4 git ls-files not available (not a git repo?)')
    _mark[0] = len(failures)
    if (root / '.gitmodules').exists():
        fail('B4 .gitmodules present')
    # B8: .gitattributes
    for p in paths:
        if p.name == '.gitattributes':
            fail(f'B8 .gitattributes present: {p.relative_to(root)} (card: none allowed)')
    # B5/B6/B7: names
    lower_seen: dict[str, Path] = {}
    for r in rel:
        name = r.name
        if name.lower() in SYSTEM_FILES:
            fail(f'B5 system file: {r}')
        if ':' in name or name.endswith(('.', ' ')) or name.split('.')[0].lower() in WIN_DEVICES:
            fail(f'B6 name not valid on Windows/macOS: {r}')
        if re.search(r'[<>"|?*\\\x00-\x1f]', name):
            fail(f'B6 reserved character in name: {r}')
        key = str(r).lower()
        if key in lower_seen:
            fail(f'B6 case-only duplicate: {r} vs {lower_seen[key]}')
        lower_seen[key] = r
        if (root / r).is_dir() and not re.fullmatch(r'[A-Za-z0-9._-]+', name):
            fail(f'B7 folder name has characters outside [A-Za-z0-9._-]: {r}')
    if not re.fullmatch(r'[A-Za-z0-9._-]+', root.resolve().name):
        fail(f'B7 plugin folder name: {root.resolve().name}')

    _mark[0] = len(failures)
    # B9/E1/E2/E3/E12: sizes and types
    total = 0
    for p in files:
        data = p.read_bytes()
        size = len(data)
        total += size
        r = p.relative_to(root)
        ext = p.suffix.lower()
        if size >= 5 * MIB:
            fail(f'B9 file >= 5 MiB: {r}')
        if ext in IMAGE_EXT:
            if not is_complete_image(p, data):
                fail(f'E3 image is not a complete {ext}: {r}')
        elif ext in FONT_EXT:
            pass
        else:
            if size >= 256 * KIB:
                fail(f'E1 non-image file >= 256 KiB: {r} ({size} B)')
            try:
                data.decode('utf-8')
            except UnicodeDecodeError:
                fail(f'E3 binary file that is not an image/font: {r}')
            if ext in {'.js', '.mjs', '.cjs', '.css'} and max((len(x) for x in data.splitlines()), default=0) > 500:
                fail(f'E12 looks minified (line > 500 chars): {r}')
    if len(files) > 512:
        fail(f'E2 {len(files)} files > 512')
    if total >= MIB:
        fail(f'card: bundle {total} B >= 1 MiB')
    ok(f'B9/E1/E2 {len(files)} files, {total} B total; largest {max((p.stat().st_size for p in files), default=0)} B')

    _mark[0] = len(failures)
    # E5/E6/E7/E9: what it runs
    names = {p.name for p in files}
    for cfg in PKG_CONFIGS & names:
        fail(f'E6 package-manager config present: {cfg}')
    if (root / 'package.json').exists() and any((root / lf).exists() for lf in LOCKFILES):
        fail('E7 package.json + lockfile at the plugin root')
    for d in ('hooks', 'scripts', 'bin'):
        if (root / d).exists():
            fail(f'E: {d}/ present; this bundle ships Markdown/JSON/images only')
    text_files = [p for p in files if p.suffix.lower() not in IMAGE_EXT | FONT_EXT]
    for p in text_files:
        t = p.read_text('utf-8', errors='replace')
        r = p.relative_to(root)
        if p.name in {'.mcp.json', 'plugin.json', 'hooks.json'} and LAUNCHERS.search(t):
            fail(f'E5 package launcher in {r}')
        if re.search(r'\$\{?[A-Z][A-Z0-9_]*(TOKEN|KEY|SECRET|PASSWORD)\}?', t):
            fail(f'E9 reads a credential from the environment: {r}')
        for pat in SECRET_PATTERNS:
            m = pat.search(t)
            if m:
                fail(f'E8 possible secret in {r}: {m.group(0)[:24]}…')
        if is_tooling(r):
            continue
        m = INTERNAL_HINTS.search(t)
        if m and p.name != '.gitignore':
            fail(f'public-safe: internal reference "{m.group(0)}" in {r}')
        for host in re.findall(r'https?://([A-Za-z0-9.-]+)', t):
            if host.lower() not in ALLOWED_HOSTS:
                fail(f'public-safe: URL host {host} in {r} is not in {sorted(ALLOWED_HOSTS)}')
    ok('E5/E6/E7/E8/E9 no launchers, package configs, lockfiles, env credentials or secret patterns')

    _mark[0] = len(failures)
    # E4/E10/E11: .mcp.json
    mcp_path = root / '.mcp.json'
    try:
        mcp = json.loads(mcp_path.read_text('utf-8'))
        servers = mcp['mcpServers']
        for key, s in servers.items():
            if s.get('type') not in ('http', 'sse', 'ws'):
                fail(f'E10 server {key}: type {s.get("type")!r}')
            if not str(s.get('url', '')).startswith(('https://', 'wss://')):
                fail(f'E10 server {key}: url not https')
            if 'headers' in s or 'command' in s or 'env' in s:
                fail(f'E8/E4 server {key}: headers/command/env present')
        if [s.get('url') for s in servers.values()] != [MCP_URL] or list(servers) != [MCP_KEY]:
            fail(f'E11 expected exactly {{"{MCP_KEY}": {MCP_URL}}}, got {servers}')
        else:
            ok(f'E4/E10/E11 .mcp.json = {MCP_KEY} → {MCP_URL} (type http, no headers)')
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        fail(f'E10 .mcp.json unreadable: {exc}')

    _mark[0] = len(failures)
    # C1/C5/C7 + lint: manifest
    try:
        man = json.loads((root / '.claude-plugin' / 'plugin.json').read_text('utf-8'))
        name = man.get('name', '')
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?', name):
            fail(f'C1 name {name!r} breaks the pattern')
        if name in {'claude', 'anthropic', 'official', 'plugin', 'mcp', 'test'}:
            fail('C2 reserved name')
        for field in ('displayName', ('author', 'name')):
            val = man.get(field) if isinstance(field, str) else (man.get(field[0]) or {}).get(field[1])
            if not isinstance(val, str) or not val.isascii() or re.search(r'[​-‏⁠﻿]', val):
                fail(f'C5 {field} must be plain ASCII (one writing system): {val!r}')
        for field in ('description', 'author', 'version'):
            if not man.get(field):
                fail(f'C7 {field} missing')
        if any(BANNED_KEYWORDS.search(k) for k in man.get('keywords', [])):
            fail('lint: keywords contain advice/advisor/retirement')
        if not ((root / 'LICENSE').is_file() or man.get('license')):
            fail('D2 no LICENSE file and no license field')
        # Directory listing fields (plugins-reference "Directory listing fields"): each URL an https:// URL on our hosts,
        # the icon an image file inside the plugin. Claude Code ignores them; the portal's Listing details reads them.
        for field in LISTING_URLS:
            url = man.get(field)
            if url is None:
                continue
            host = re.match(r'https://([A-Za-z0-9.-]+)(/|$)', str(url))
            if not host or host.group(1).lower() not in ALLOWED_HOSTS:
                fail(f'listing {field} must be an https:// URL on {sorted(ALLOWED_HOSTS)}: {url!r}')
        icon = man.get('icon')
        if icon is not None:
            ipath = (root / str(icon)).resolve()
            if not str(icon).startswith('./') or root.resolve() not in ipath.parents:
                fail(f'listing icon must be a ./ path inside the plugin: {icon!r}')
            elif not ipath.is_file() or ipath.suffix.lower() not in IMAGE_EXT or not is_complete_image(ipath, ipath.read_bytes()):
                fail(f'listing icon is not a complete image file: {icon!r}')
        ok(f'C1/C5/C7/D2 manifest name={name} displayName={man.get("displayName")!r} license={man.get("license")}')
    except (OSError, ValueError) as exc:
        fail(f'C plugin.json unreadable: {exc}')

    _mark[0] = len(failures)
    # D1/D3/D4: README
    readme = root / 'README.md'
    if not readme.is_file():
        fail('D1 README.md missing')
    else:
        t = readme.read_text('utf-8')
        n = readme_words(t)
        if n < 40:
            fail(f'D1 README has {n} words outside code blocks (< 40)')
        for label, s in (('D14', D14), ('D15', D15)):
            if s not in t:
                fail(f'{label} block missing from README')
        manifest_text = (root / '.claude-plugin' / 'plugin.json').read_text('utf-8')
        for label, text in (('README.md', t), ('plugin.json', manifest_text)):
            m = NOT_LISTED_YET.search(re.sub(r'<!--.*?-->', ' ', text, flags=re.S))
            if m:
                fail(f'D28 "{m.group(0)}" in {label}: no directory or listing words before the plugin is listed')
        for img in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', t):
            if not img.startswith('http') and not (root / img).is_file():
                fail(f'D4 README image not found: {img}')
        ok(f'D1/D3 README {n} words outside code blocks; D14 and D15 present')

    # F1/F2: skills
    skills = root / 'skills'
    _mark[0] = len(failures)
    for sk in sorted(skills.iterdir()) if skills.is_dir() else []:
        _mark[0] = len(failures)
        md = sk / 'SKILL.md'
        if not md.is_file():
            fail(f'F2 {sk.relative_to(root)}/SKILL.md missing (exact spelling)')
            continue
        t = md.read_text('utf-8')
        m = re.match(r'---\n(.*?)\n---\n', t, re.S)
        if not m:
            fail(f'F1 {md.relative_to(root)}: no YAML front matter')
            continue
        try:
            import yaml  # type: ignore[import-untyped]

            fm = yaml.safe_load(m.group(1))
        except ImportError:
            fm = dict(re.findall(r'^(\w+):\s*"?(.*?)"?\s*$', m.group(1), re.M))
        if not isinstance(fm, dict) or not isinstance(fm.get('description'), str):
            fail(f'F1 {md.relative_to(root)}: description must be one string')
        elif fm.get('name') != sk.name:
            fail(f'F1 {md.relative_to(root)}: name {fm.get("name")!r} != folder {sk.name!r}')
        else:
            ok(f'F1 skills/{sk.name}: front matter OK ({len(fm["description"])} chars)')


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1]).expanduser()
    check(root)
    for n in notes:
        print(f'ok    {n}')
    for f in failures:
        print(f'FAIL  {f}')
    print(f'{len(failures)} failure(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
