# Contributing

## Getting started

### Clone this repository
1. See [clone the repository](https://help.github.com/articles/cloning-a-repository/) for how to clone the repo to your local machine so you can begin making changes.
1. On your local machine make sure you have the latest version of the `master` branch:

    ```
    git checkout master
    git pull upstream master
    ```

### Install development dependencies

See 1-4 [here in main Genie](https://github.com/Sage-Bionetworks/Genie#developing-locally) to install the dependencies required.

#### Annotation dependencies
If you are updating any part of the `annotation_suite_wrapper.sh` script, you will need to 


## The development life cycle

### Development

1. Create a feature branch off the `master` branch. If there is a GitHub/JIRA issue that you are addressing, name the branch after the issue with some more detail (like `{GH|JIRA}-123-add-some-new-feature`).

    ```
    git checkout master
    git checkout -b JIRA-123-new-feature
    ```

2. Make any relevant changes. 

3. Proceed on to **Testing**

4. Once you have completed all the steps above, in Github, create a pull request from your feature branch to the `master` branch of Sage-Bionetworks/Genie.

> *A code maintainer must review and accept your pull request.*

This package uses [semantic versioning](https://semver.org/) for releasing new versions. The version should be updated on the `master` branch as changes are reviewed and merged in by a code maintainer.

### Testing

#### Unit Tests

Run tests for python script(s) after development by:

1. Install `pytest` via [here](https://docs.pytest.org/en/6.2.x/getting-started.html#install-pytest)
2. Running the following:

```
pytest test
```

Run tests for bash script(s) after development by:

1. Install `bats` via [here](https://bats-core.readthedocs.io/en/stable/installation.html)
2. Running the following:

```
bats test
```

#### Integration Test

Be sure to run the relevant parts of the test main genie pipeline as part of [these instructions](https://github.com/Sage-Bionetworks/Genie/#developing-locally) that would be affected by changes to this repo.

#### Testing annotator shell script changes

If you are making any changes to the `annotation_suite_wrapper.sh` script, please see here for testing that: [Updating the annotation shell script in annotation-tools](https://sagebionetworks.jira.com/wiki/spaces/APGD/pages/3016687662/Variant+Annotation#Updating-the-annotation-shell-script-in-annotation-tools)

#### Testing updated annotator.jar file

If you are updating the `annotator.jar` file, please see here for how to go about testing that using this repo: [Variant Annotation](https://sagebionetworks.jira.com/wiki/spaces/APGD/pages/3016687662/Variant+Annotation)

#### Docker

Make sure this runs on the main Genie docker image by pulling down the docker image and running the relevant parts of the code in it. See [main Genie Dockerhub](https://github.com/Sage-Bionetworks/Genie/blob/main/CONTRIBUTING.md#dockerhub) for where to find this.

If you need to make updates to the Genie docker image as part of the development on this repo, make sure you're using the rebuilt version of the docker image when testing.

### Release Procedure (For Package Maintainers)

Follow gitflow best practices as linked above.

1. Always merge all new features into `master` branch first (unless it is a documentation, readme, or github action patch into `master`)
1. Create release tag (`v...`) and a brief message
1. Push tag and change(s) from `master`
1. Create a new release on the repo. Include release notes.  Also include any known bugs for each release here.
1. Follow the [release procedure in main Genie](https://github.com/Sage-Bionetworks/Genie/blob/main/CONTRIBUTING.md#release-procedure-for-package-maintainers) for re-tagging annotation-tools repo on main GENIE with the newest release