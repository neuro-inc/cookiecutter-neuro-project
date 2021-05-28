[comment]: # (Please do not modify this file)
[comment]: # (Put your comments to changelog.d and it will be moved to changelog in next release)
[comment]: # (Clear the text on make release for canceling the release)

[comment]: # (towncrier release notes start)


No significant changes.


Neuro Platform Project Template v21.04.12 (2021-04-12)
======================================================

Features
--------


- Pin neuro-actions' versions used in the template ([#458](https://github.com/neuro-inc/cookiecutter-neuro-project/issues/458))


Neuro Platform Project Template v20.12.30 (2020-12-30)
======================================================

Bugfixes
--------


- Fix volumes mounting point references for train and multi-train jobs. ([#430](https://github.com/neuro-inc/cookiecutter-neuro-project/issues/430))


Improved Documentation
----------------------


- Added towncrier for changelogs generation, changed versioning style to date-based. ([#431](https://github.com/neuro-inc/cookiecutter-neuro-project/issues/431))


### v1.8 (15-12-2020)
```
c160e5a Restore preset for jupyter
6366007 Remove invalid preset from jupyter action
d1f90d9 Update default preset
e7db9c5 Update default preset
e92f922 [docs] Update RELEASE.md
995f776 Update neuro-cli pypi package name (#429)
4bb156c Add the preset into args. (#428)
73ce733 Fix typo in live.yaml
65e21ba [docs] Update internal docs (#427)
866b8aa Migrate to external neuro-flow actions (#425)
6dd7045 Bump cryptography from 2.8 to 3.2 (#424)
448c2e7 [Template] Migrate template from makefile to neuro-flow (#419)
94e218b [Tests] Support new job status in tests (#418)
```

### v1.7.6 (28-08-2020)
```
618ea84 [Makefile] bump base_image to v1.7.6
f8cc2f6 [tests] Drop filebrowser test (#416)
61847d1 [tests] Rename the Makefile target "init" to "setup" (#409)
99addfa [tests] Delete tqdm test (#415)
400757f [tests] Drop W&B completely (#411)
79b4ff1 [tests] Fix tests (#410)
3b4814f [tests] Update tests
```

### v1.7 (30-07-2020)
```
890d690 [docs] Update docs (#408)
537f20e [Makefile] Remove hypertrain (#407)
644151d [Makefile] Secrets support (#400)
414053c Fix version
5dce8dd [Makefile] Bump base env version to v1.7 (#405)
8650a7a [tests] Drop flaky tests on W&B and hypertrain (#406)
84b3a06 [doc] Add release instructions (#404)
2b8a681 [Makefile, tests] Adapt Makefile to neuro>=20.6.23, Simplify tests (#398)
```

### v1.6.1 (17-06-2020)
```
e3d910b [Makefile] No upload-notebooks before each command (#396)
70ba4a3 Disable life-span for Jupyter job (#397)
```

### v1.6 (18-05-2020)
```
4b0b20b [Makefile] Stabilize W&B Hypertrain + Set up CI for MacOS (#390)
bd988f3 [Makefile] Sync directories optionally (#386)
099d601 [tests] Use tags instead of image names (#391)
31969f7 [tests] Switch tests on AWS (#392)
e60fb2b Minor improvements to simplify NNI integration (#389)
c0558a1 [Makefile] Bump base env version to v1.5
```
