#!/usr/bin/env bash
# Secret scan for this plugin (`make secrets`, part of `make check`): the full git history of every ref and the
# working tree, with .github/gitleaks.toml (gitleaks default rules plus a few extra ones). No baseline: this
# repository must stay at 0 findings. Values are always redacted.
# Uses $GITLEAKS if it reports the pinned GITLEAKS_VERSION (.github/tool-versions.env), else downloads that release
# once into ${CI_TOOLS_DIR:-~/.cache/divid-ci}/gitleaks-<version>/ and verifies it against the release checksums.
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
set -a; . "$root/.github/tool-versions.env"; set +a
v="$GITLEAKS_VERSION"
tools="${CI_TOOLS_DIR:-$HOME/.cache/divid-ci}"

bin="${GITLEAKS:-}"
if [ -z "$bin" ] || [ "$("$bin" version 2>/dev/null)" != "$v" ]; then
  bin="$tools/gitleaks-$v/gitleaks"
  if [ ! -x "$bin" ]; then
    case "$(uname -s)-$(uname -m)" in
      Linux-x86_64) plat=linux_x64 ;; Linux-aarch64) plat=linux_arm64 ;;
      Darwin-arm64) plat=darwin_arm64 ;; Darwin-x86_64) plat=darwin_x64 ;;
      *) echo "gitleaks.sh: unsupported platform $(uname -sm)" >&2; exit 2 ;;
    esac
    tar="gitleaks_${v}_${plat}.tar.gz"
    base="https://github.com/gitleaks/gitleaks/releases/download/v$v"
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    curl -fsSL -o "$tmp/$tar" "$base/$tar"
    curl -fsSL -o "$tmp/sums" "$base/gitleaks_${v}_checksums.txt"
    (cd "$tmp" && grep " $tar\$" sums | sha256sum -c - >&2)
    mkdir -p "$tools/gitleaks-$v"
    tar -xzf "$tmp/$tar" -C "$tools/gitleaks-$v" gitleaks
  fi
fi
[ "$("$bin" version)" = "$v" ] || { echo "gitleaks.sh: $bin is not v$v" >&2; exit 2; }

cd "$root"
cfg=.github/gitleaks.toml
rc=0
echo "gitleaks v$v git . (all refs)"
"$bin" git . --log-opts=--all --no-banner --redact --config "$cfg" || rc=1
echo "gitleaks v$v dir ."
"$bin" dir . --no-banner --redact --config "$cfg" || rc=1
exit "$rc"
