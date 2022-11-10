#!/bin/bash
# Usage: ./scripts/release.sh <major|minor|patch>
set -ex

if [ $# -ne 1 ]; then
  echo "Usage: ./release.sh <major|minor|patch>"
  exit 1
fi

hatch version $1
git add src/__init__.py
# Fail if there are any unstaged changes left
git diff --exit-code
git commit -am "Release v$1 🚀"
git tag v$1 -m "Release v$1 🚀"
git push --follow-tags
hatch build
hatch publish
gh release create v$1 -t "v$1" -d
