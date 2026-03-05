# Releasing Guide

This document aims to guide the maintainers on how to release a new version of `circuit-maintenance-parser`.

## 1. Prepare the Release

1. Create a release branch off of `develop`:

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release-vX.Y.Z
   ```

2. Generate the release notes using `towncrier`. This will consolidate all the fragment files in `changes/` into `docs/release_notes.md` and remove the fragments:

   ```bash
   poetry run towncrier build --version X.Y.Z
   ```

3. Bump the project version using `poetry`:

   ```bash
   poetry version {patch/minor/major}
   ```

4. Commit the changes:

   ```bash
   git add docs/release_notes.md pyproject.toml changes/
   git commit -m "Release vX.Y.Z"
   git push origin release-vX.Y.Z
   ```

## 2. Pull Request

1. Open a Pull Request from your `release-vX.Y.Z` branch targeting **`main`**.
2. Ensure all CI checks pass.
3. Once approved, merge the Pull Request into `main`.

## 3. Create Release

1. Once the code is merged to `main`, navigate to the GitHub repository's "Releases" page.
2. Draft a new release.
3. Create a new tag `vX.Y.Z` (ensure it matches the version in `pyproject.toml`).
4. Paste the content from the "Release Overview" section of `docs/release_notes.md` into the release description.
5. Publish the release.

## 4. Backport to Develop

After the release is published, the changes (changelog updates and version bump) need to be synced back to the development branch.

1. Open a Pull Request from `main` targeting **`develop`**.
2. Merge the Pull Request.
