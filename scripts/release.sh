#!/bin/bash
# Usage: ./scripts/release.sh <major|minor|patch>
set -ex

if [ $# -ne 1 ]; then
  echo "Usage: ./release.sh <major|minor|patch>"
  exit 1
fi

hatch version $1
NEW_VERSION=$(hatch version)
git add src/pytest_codspeed/__init__.py
# Fail if there are any unstaged changes left
git diff --exit-code
git commit -am "Release v$NEW_VERSION 🚀"
git tag v$NEW_VERSION -m "Release v$NEW_VERSION 🚀"
git push --follow-tags
