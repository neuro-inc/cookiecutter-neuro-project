Release instructions
====================

Neuro CLI [uses `release` branch](https://github.com/neuromation/platform-client-python/blob/d00a75504d665acdbcdda24f3999ee4b2223054d/neuromation/cli/project.py#L43-L48) to scaffold projects, so to do a release we need to update `release` branch.


Instructions:
------------

1. Merge all necessary PRs and ensure that `master` is green, update your local master branch:
    ```
    $ git checkout master
    $ git pull origin
    ```
2. Test `master` manually:
    ```
    $ cookiecutter gh:neuromation/cookiecutter-neuro-project -c master
    project_name [Neuro Project]: 
    project_slug [neuro-project]: 
    code_directory [modules]: 
    $ cd neuro-project
    $ ls
    apt.txt  config  data  Dockerfile  HELP.md  modules  notebooks  README.md  requirements.txt  results  setup.cfg
    $ neuro-flow build myimage
    $ neuro-flow run jupyter
    ...
    ```
3. Generate changelog:
    - `make changelog-draft` - verify changelog looks valid
    - `make changelog` - delete changelog items from `CHANGELOG.d` and really modify [CHANGELOG.md](./CHANGELOG.md)
    - `git add CHANGELOG* && git commit -m "Update changelog"` - commit changelog changes in **local** repository
    - `git tag v$(date +"%y.%m.%d")` - mark latest changes as a release tag
    - `git push && git push --tags` - push the updated changelog and assigned tag to the remote repository 
    - Note, this `master` branch update will trigger CI

4. Now, hard-reset `release` branch on `master` (actual release):
    ```
    $ git checkout release
    $ git reset --hard master
    $ git push  # no need to push --force since `release` will move only forward
    ```
5. Once `release` is green, test it via `neuro project init`, and if everything's fine,
    publish new release to Slack: `#platform-development`, `#platform-feedback`, `#template-nightly-testing`.

Notes:
------

- When CI is triggered:
    - Each open PR (even draft PR) agains `master`.
    - Each new commit to `master` and `release`.
    - Nightly builds: `master` at 00:00 and `release` at 01:00 UTC.
- Branches `master` and `release` are tested against `staging` (`neuro-public` cluster), whereas all other branches are tested against `dev`.
- See [here](https://dev.azure.com/neuromation/cookiecutter-neuro-project/_build?definitionId=4) to access builds on Azure Pipelines.
