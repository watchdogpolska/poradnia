#!/usr/bin/env bash
# Verify that the Python version pinned in different places hasn't drifted
# apart (e.g. a Dockerfile bump without matching tooling targets). Every pin
# must be found and must resolve to the same X.Y version.
# Used by `make check-python-versions` and the python_version_check CI job.
cd "$(dirname "$0")/.." || exit 1

status=0
versions=""
pin() {
  # $1 = label, $2 = extracted X.Y version (empty if not found)
  if [ -z "$2" ]; then
    echo "::error::$1: Python version pin not found"
    status=1
  else
    echo "$1: $2"
    versions="$versions $2"
  fi
}
for f in .contrib/docker/Dockerfile.web \
         .contrib/docker/Dockerfile.web.production \
         .contrib/docker/Dockerfile.maildump; do
  pin "$f (ARG PYTHON_VERSION)" "$(sed -nE \
    "s/^ARG PYTHON_VERSION=['\"]?([0-9]+\.[0-9]+)['\"]?\s*$/\1/p" "$f")"
done
pin ".readthedocs.yml (build.tools.python)" "$(sed -nE \
  's/^\s+python:\s*"?([0-9]+\.[0-9]+)"?\s*$/\1/p' .readthedocs.yml)"
pin "pyproject.toml (black target-version)" "$(sed -nE \
  "s/^target-version = \['py3([0-9]+)'\]\s*$/3.\1/p" pyproject.toml)"
pin ".pre-commit-config.yaml (pyupgrade)" "$(sed -nE \
  's/^\s+- --py3([0-9]+)-plus\s*$/3.\1/p' .pre-commit-config.yaml)"
pin "setup.py (python_requires)" "$(sed -nE \
  's/^\s+python_requires=">=([0-9]+\.[0-9]+)",\s*$/\1/p' setup.py)"
unique=$(echo $versions | tr ' ' '\n' | sort -u)
if [ "$(echo "$unique" | grep -c .)" -gt 1 ]; then
  echo "::error::Pinned Python versions differ:" $unique
  status=1
fi
exit $status
