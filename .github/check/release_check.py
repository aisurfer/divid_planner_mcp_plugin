"""Release gate for this plugin (`make release-check`): run it before every push to the tracked branch.

The directory follows one branch of this repository (the tracked branch, `main`) and scans every new commit there as a
new version. So a push to `main` is a release, and this check refuses one that isn't ready:

- the working tree is clean and HEAD is on the tracked branch (TRACKED, default `main`);
- `origin` is the plugin's repository (REPO, default github.com/aisurfer/divid_planner_mcp_plugin);
- `version` in .claude-plugin/plugin.json is X.Y.Z and at least 1.0.0 (the first directory version);
- it is above every `vX.Y.Z` tag, or its own tag `v<version>` already points at HEAD (a re-run after tagging):
  raise `version` with every release (patch: wording or skill fixes; minor: a new skill or a new tool the skills use;
  major: a change that breaks how the plugin is used), then tag the commit `v<version>`.

Usage: python3 .github/check/release_check.py [.]   (exit 1 on any failure; `make release-check` also runs `make check`)
"""
import json
import os
import re
import subprocess
import sys

TRACKED = os.environ.get('TRACKED', 'main')
REPO = os.environ.get('REPO', 'aisurfer/divid_planner_mcp_plugin')
SEMVER = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
root = sys.argv[1] if len(sys.argv) > 1 else '.'
failures = []


def git(*args):
    return subprocess.run(['git', '-C', root, *args], capture_output=True, text=True).stdout.strip()


def fail(msg):
    failures.append(msg)
    print(f'FAIL  {msg}')


def ok(msg):
    print(f'ok    {msg}')


branch = git('rev-parse', '--abbrev-ref', 'HEAD')
(ok if branch == TRACKED else fail)(f'on the tracked branch {TRACKED} (HEAD is on {branch})')
dirty = git('status', '--porcelain')
(ok if not dirty else fail)('clean working tree' + ('' if not dirty else f': {len(dirty.splitlines())} changed path(s)'))
origin = git('remote', 'get-url', 'origin')
want = re.compile(rf'(github\.com[:/]){re.escape(REPO)}(\.git)?$')
(ok if want.search(origin) else fail)(f'origin is {REPO} ({origin or "none"})')

with open(os.path.join(root, '.claude-plugin', 'plugin.json'), encoding='utf-8') as f:
    version = json.load(f).get('version', '')
m = SEMVER.match(version)
if not m:
    fail(f'plugin.json version "{version}" is X.Y.Z')
else:
    v = tuple(int(x) for x in m.groups())
    (ok if v >= (1, 0, 0) else fail)(f'version {version} is 1.0.0 or above (the first directory version is 1.0.0)')
    tags = {}
    for t in git('tag', '--list', 'v*').split():
        tm = SEMVER.match(t[1:])
        if tm:
            tags[tuple(int(x) for x in tm.groups())] = t
    head = git('rev-parse', 'HEAD')
    own = tags.get(v)
    if own:
        at = git('rev-list', '-n', '1', own)
        (ok if at == head else fail)(f'tag {own} points at HEAD' + ('' if at == head else f' (it is on {at[:7]}): raise version'))
    newest = max(tags) if tags else None
    if newest and not own:
        (ok if v > newest else fail)(f'version {version} is above the newest tag {tags[newest]}')
    if not tags:
        ok('no release tag yet: this is the first release')

print('release-check: ' + ('FAILED' if failures else 'ready'))
sys.exit(1 if failures else 0)
