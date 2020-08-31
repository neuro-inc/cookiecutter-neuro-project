Release instructions
====================

Neuro CLI [uses `release` branch](https://github.com/neuromation/platform-client-python/blob/d00a75504d665acdbcdda24f3999ee4b2223054d/neuromation/cli/project.py#L43-L48) to scaffold projects, so to do a release we need to update `release` branch.


Preconditions:
------------
1. All necessary PRs are merged into `master` branch and CI tests are green.

Release process:
------------

1. Update your local `master` branch.
```bash
$ git checkout master
$ git pull origin
```

2. Ensure base image [version](./{{cookiecutter.project_slug}}/Makefile#L2)
is the latest available (see [Neuro Platform Base Image](https://github.com/neuromation/neuro-base-environment/releases)).
Update template [version](./{{cookiecutter.project_slug}}/Makefile#L1), it may reflect the version of used base image.

Hint: base image version could be get with
```bash
$ BASE_IMAGE_VERSION=$(git ls-remote --tags --refs --sort="version:refname" git://github.com/neuromation/neuro-base-environment.git | awk -F/ 'END{print$NF}')
$ echo $BASE_IMAGE_VERSION
1.7
```

3. Test `master` manually:
```bash
$ cookiecutter gh:neuromation/cookiecutter-neuro-project -c master
project_name [Neuro Project]: 
project_slug [neuro-project]: 
code_directory [modules]: 
$ cd neuro-project
$ ls
apt.txt  config  data  HELP.md  Makefile  modules  notebooks  README.md  requirements.txt  results  setup.cfg
$ make setup
...
```
4. If `master` is fine, find out what was the previous release (find latest tag like `v1.6` or `v1.6.1`) and save the following information to `CHANGELOG.md`. Suppose we're releasing version `v1.7`:
```bash
$ PREV=$(git tag --list | grep -e "v.*" | tail -1)
$ echo $PREV
v1.6.1
$ git log --oneline $PREV..HEAD   # See the changes
4b0b20b [Makefile] Stabilize W&B Hypertrain + Set up CI for MacOS (#390)
bd988f3 [Makefile] Sync directories optionally (#386)
099d601 [tests] Use tags instead of image names (#391)
31969f7 [tests] Switch tests on AWS (#392)
e60fb2b Minor improvements to simplify NNI integration (#389)
c0558a1 [Makefile] Bump base env version to v1.5
```
5. Put the lines above^ to `CHANGELOG.md` under the heading `### v1.7 (todays-date)` and push these changes to `master`:
```bash
$ git add CHANGELOG.md 
$ git commit -m "Update changelog" 
$ git push
$ git tag v1.7
$ git push --tags
```
Note, this update to `master` will trigger CI.

6. Now,  hard-reset `release` branch on `master`:
```bash
$ git checkout release
$ git reset --hard master
$ git push  # no need to push --force since `release` will move only forward
```
7. Once `release` is green, test it via `neuro project init`, and if everything's fine, publish new release to slack: `#platform-development`, `#platform-feedback`, `#template-nightly-testing`.


Notes:
------

- In order to ease the process of constructing the changelog, each PR should be prefixed with `[keywords]` reflecting the changes:
    - `[Makefile]` if the makefile itself was modified,
    - `[Template]` if template structure was modified,
    - `[tests]`, `[docs]` if only tests or docs were modified.
- When CI is triggered:
    - Each open PR (even draft PR) agains `master`.
    - Each new commit to `master` and `release`.
    - Nightly builds: `master` at 00:00 and `release` at 01:00 UTC.
- Branches `master` and `release` are tested against `staging` (`neuro-public` cluster), whereas all other branches are tested against `dev`.
- See [here](https://dev.azure.com/neuromation/cookiecutter-neuro-project/_build?definitionId=4) to access builds on Azure Pipelines.