#!/bin/bash
set -e

VERSION=v$BUMPVER_NEW_VERSION

git tag v$VERSION -m "Release v$VERSION 🚀"
git push --follow-tags
