# Pre-submission checks for this plugin. The same `make check` runs locally and in .github/workflows/validate.yml.
# Needs python3 and node; the first run downloads the pinned Claude Code CLI (npx) and gitleaks.
# Tool versions come only from .github/tool-versions.env.
#
#   make check      every check below; each one runs even after a failure, the failed ones are listed at the end
#   make validate   claude plugin validate --strict . (pinned Claude Code CLI; warnings fail too)
#   make files      layout, names, sizes, file types, .mcp.json, manifest, README, skills (.github/check/check_bundle.py)
#   make copy       wording lint over README, skills and plugin.json (.github/check/copy_lint.mjs)
#   make secrets    gitleaks over the full history and the working tree (.github/check/gitleaks.sh)
#   make release-check  before every push to the tracked branch `main` (each commit there is a new directory version):
#                   clean tree on main, origin = the plugin repo, version X.Y.Z >= 1.0.0 and above every v* tag
#                   (.github/check/release_check.py), then `make check`
include .github/tool-versions.env

.PHONY: check validate files copy secrets release-check

check:
	@failed=""; for t in validate files copy secrets; do \
	  echo "--- check: $$t"; $(MAKE) --no-print-directory $$t || failed="$$failed $$t"; done; \
	  if [ -n "$$failed" ]; then echo "check: FAILED:$$failed"; exit 1; fi; echo "check: all passed"

validate:
	npx -y @anthropic-ai/claude-code@$(CLAUDE_CODE_VERSION) --version
	npx -y @anthropic-ai/claude-code@$(CLAUDE_CODE_VERSION) plugin validate --strict .

files:
	python3 .github/check/check_bundle.py .

copy:
	node .github/check/copy_lint.mjs .

secrets:
	bash .github/check/gitleaks.sh

release-check:
	python3 .github/check/release_check.py .
	@$(MAKE) --no-print-directory check
