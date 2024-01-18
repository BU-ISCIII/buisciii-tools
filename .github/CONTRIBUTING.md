# buisciii-tools: Contributing Guidelines

## Contribution workflow

If you'd like to write or modify some code for buisciii-tools, the standard workflow is as follows:

1. Check that there isn't already an issue about your idea in the [buisciii-tools issues](https://github.com/BU-ISCIII/buisciii-tools/issues) to avoid duplicating work. **If there isn't one already, please create one so that others know you're working on this**
2. [Fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) the [buisciii-tools repository](https://github.com/BU-ISCIII/buisciii-tools/) to your GitHub account
3. Make the necessary changes / additions within your forked repository following the [code style guidelines](#code-style-guidelines)
4. Modify the `CHANGELOG` file according to your changes.
5. Update any documentation as needed.
6. [Submit a Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) against the `develop` or `hotfix` branch and sent the url to the #pipelines-dev channel in slack (if you are not in the slack channel just wait fot the PR to be reviewed and rebased).

If you're not used to this workflow with git, you can start with:

- Some [docs in the bu-isciii wiki](https://github.com/BU-ISCIII/BU-ISCIII/wiki/Github--gitflow)
- [some slides](https://docs.google.com/presentation/d/1PruqGxPQVxtNcuEbOd86mylXorgYIU5a/edit?pli=1#slide=id.p1) (in spanish) 
- some github generic docs [docs from GitHub](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests)
- even their [excellent `git` resources](https://try.github.io/).

### buisciii-tools repo branches

buisciii-tools repo works with a three branching scheme. Two regular branches `main` and `develop`, and a third one created for hot fixes `hotfix`. This last one is created for changes in the **services templates**.

- `main`: stable code only for releases.
- `develop`: new code development for the diferente modules
- `hotfix`: bug fixing and/or templates addition/modification (bash scripts in: `templates` folder)

You need to submit your PR always against `develop` or `hotfix` depending on the nature of your changes. Once approbed, this changes must be **`rebased`** so we do not create empty unwanted merges.

## Tests

When you create a pull request with changes, [GitHub Actions](https://github.com/features/actions) will run automatic tests.
Typically, pull-requests are only fully reviewed when these tests are passing, though of course we can help out before then.

There are typically two types of tests that run:

### Lint tests

We use black and flake8 linting based on PEP8 guidelines. You can check more information [here](https://github.com/BU-ISCIII/BU-ISCIII/wiki/Python#linting)

### Code tests

TODO. NOT YET IMPLEMENTED.
Anyhow you should always submit locally tested code!!

### New version bumping and release

In order to create a new release you need to follow the next steps:

1. Set the new version according to [semantic versioning](https://semver.org/), in our particular case, changes in the `hotfix` branch will change the PATCH version (third one), and changes in develop will typicaly change the MINOR version, unless the developing team decides otherwise.
2. Create a PR bumping the new version against `hotfix` or `develop`. For bumping a new version just change [this line](https://github.com/BU-ISCIII/buisciii-tools/blob/615f1390d96cd6c8168acebc384289520a3cd728/setup.py#L5) with the new version.
3. Once that PR is merged, create via web another PR against `main` (origin `develop` or `hotfix` accordingly). This PR would need 2 approvals.
4. [Create a new release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) copying the appropiate notes from the `CHANGELOG`.
5. Once the release is approved and merged, you're all set! 

PRs from one branch to another, like in a release should be **`merged`** not rebased, so we avoid conflicts and the branch merge is correctly visualize in the commits history.

> A new PR for `develop` branch will be automatically generated if the changes came from `hotfix` so everything is properly sync.

### Code style guidelines

We follow PEP8 conventions as code style guidelines, please check [here](https://github.com/BU-ISCIII/BU-ISCIII/wiki/Python#pep-8-guidelines-read-the-full-pep-8-documentation) for more detail.

## Getting help

For further information/help, please ask on the  `#pipelines-dev` slack channel or write us an email! (bionformatica@isciii.es)