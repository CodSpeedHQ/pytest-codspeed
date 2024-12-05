#!/bin/bash
set -e

VERSION=$BUMPVER_NEW_VERSION

# We handle tagging here since bumpver doesn't allow custom
# tagnames and we want a v prefix
git tag v$VERSION -m "Release v$VERSION 🚀"
git push --follow-tags
