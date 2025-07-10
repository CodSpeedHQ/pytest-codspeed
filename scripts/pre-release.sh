#!/bin/bash
set -e

VERSION=v$BUMPVER_NEW_VERSION

# Skip alpha/beta/rc changelog generation
if [[ $VERSION == *"alpha"* ]] || [[ $VERSION == *"beta"* ]] || [[ $VERSION == *"rc"* ]]; then
    echo "Skipping changelog generation for alpha/beta/rc release"
else
    echo "Generating changelog for $VERSION"
    # Check that GITHUB_TOKEN is set
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "GITHUB_TOKEN is not set. Trying to fetch it from gh"
        GITHUB_TOKEN=$(gh auth token)
    fi
    git cliff --unreleased --tag $VERSION --prepend CHANGELOG.md
    git add CHANGELOG.md
fi

uv lock
git add uv.lock
