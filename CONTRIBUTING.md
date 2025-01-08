# Contributing

Thank you for considering contributing to this project! Here are the steps to set up your development environment:

## Install System Dependencies

Make sure you have the following system dependencies installed:

- `clang`
- `valgrind`

### Ubuntu

```sh
sudo apt-get update
sudo apt-get install clang valgrind -y
```

## Init submodules

```sh
git submodule update --init
```

## Install `uv`

Follow the [`uv` installation instructions](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) to install the tool.

## Sync Dependencies

Run the following command to sync all dependencies, including development and extras:

```sh
uv sync --all-extras --dev --locked
```

This command ensures that all necessary dependencies are installed and up-to-date.

## Running Tests

To run the tests, use the following command:

```sh
uv run pytest
```

Thank you for your contributions! If you have any questions, feel free to open an issue or reach out to the maintainers.

## Release

We use [`git-cliff`](https://git-cliff.org/) and [`bumpver`](https://github.com/mbarkhau/bumpver) to manage versioning.

Ensure you have installed `git-cliff`:

```sh
cargo binstall git-cliff
```

To release a new version, for example a patch, run the following command:

```sh
uvx bumpver update --patch --dry
```
