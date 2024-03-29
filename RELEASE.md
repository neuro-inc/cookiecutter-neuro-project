Release instructions
====================

Neuro CLI [uses `release` branch](https://github.com/neuro-inc/platform-client-python/blob/d00a75504d665acdbcdda24f3999ee4b2223054d/neuromation/cli/project.py#L43-L48) to scaffold projects, so to do a release we need to update `release` branch.


Instructions:
------------

1. Merge all necessary PRs and ensure that `master` is green, update your local master branch:
    ```
    $ git checkout master
    $ git pull origin
    ```
2. Test `master` manually:
    ```
    $ cookiecutter gh:neuro-inc/cookiecutter-neuro-project -c master
    flow_name [My flow]:
    flow_dir [neuro project]:
    flow_id [neuro_project]:
    code_directory [modules]:
    preserve Neuro Flow template hints [yes]:
    $ cd neuro project
    $ ls
    Dockerfile  HELP.md  README.md  apt.txt  config  data  modules  notebooks  requirements.txt  results  setup.cfg  update_actions.py
    $ neuro-flow build train
    $ neuro-flow upload ALL
    $ neuro-flow run jupyter
    ...
    ```
3. Generate changelog:
    - `make changelog-draft` - verify changelog looks valid
    - `make changelog` - delete changelog items from `CHANGELOG.d` and really modify [CHANGELOG.md](./CHANGELOG.md)
    - `git add CHANGELOG* version.txt`
    - `git commit -m "Update version and changelog for $(cat version.txt) release"` - commit changelog changes in **local** repository
    - `git tag $(cat version.txt)` - mark latest changes as a release tag
    - `git push && git push --tags` - push the updated changelog and assigned tag to the remote repository
    - Note, this `master` branch update will trigger CI

4. Now, hard-reset `release` branch on `master` (actual release):
    ```
    $ git checkout release
    $ git reset --hard master
    $ git push  # no need to push --force since `release` will move only forward
    ```
5. Once `release` is green, test it via `cookiecutter gh:neuro-inc/cookiecutter-neuro-project --checkout release`, and if everything's fine,
    publish new release to Slack: `#platform-feedback`.

Notes:
------

- When CI is triggered:
    - Each open PR (even draft PR) agains `master`.
    - Each new commit to `master` and `release`.
