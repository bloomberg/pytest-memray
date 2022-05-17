# Maintainance

Information useful for the maintainers of the project.

## Release process

1. Generate the release changelog via:

   ```bash
   tox r -e release -- 1.1.0
   # or
   make gen_news VERSION=1.1.0
   ```

   commit it and create a PR.

2. After merging the PR from step 1 cut a release on the GitHub release page with same version.
