# Contributing

## Releasing a New Version

To create a new version, run:

```bash
uvx bumpver update --patch  # Increment PATCH component (e.g., 1.2.3 -> 1.2.4)
uvx bumpver update --minor  # Increment MINOR component (e.g., 1.2.3 -> 1.3.0)
uvx bumpver update --major  # Increment MAJOR component (e.g., 1.2.3 -> 2.0.0)
```

### What happens

1. **Pre-release script** (`scripts/pre-release.sh`):
   - Generates the changelog using `git cliff` (skipped for alpha/beta/rc releases)
   - Updates `uv.lock`

2. **Version bump**:
   - Updates the version in `pyproject.toml` and `src/pytest_codspeed/__init__.py`
   - Creates a commit with the message "Release vX.Y.Z"

3. **Post-release script** (`scripts/post-release.sh`):
   - Creates a git tag with the `v` prefix (e.g., `v1.2.3`)
   - Pushes the commit and tag to the remote

4. **CI release workflow** (`.github/workflows/release.yml`):
   - Triggered automatically when the tag is pushed
   - Builds wheels for x86_64 and aarch64
   - Builds the source distribution
   - Publishes the package to PyPI
   - Creates a draft GitHub release
