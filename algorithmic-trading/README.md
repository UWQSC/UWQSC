# Algorithmic Trading

The University of Waterloo quantitative analytics stocks club algorithmic trading repository.

Project Board: https://github.com/orgs/UWQSC/projects/1

### Onboarding Information

###### Setup
- After cloning the repository, run the following command

```bash
chmod +x ./setup.sh
./setup.sh
```
- This sets up your:
  - Python virtual environment with your packages
  - GitHub hook for commit message regex.

###### Project Structure

- `src/`: Main code
- `interfaces/`: Abstract Interfaces, referenced by other repo
- `tests/`: Unit Tests for `src/`

Other files and directories

- `bin`: All important directory bash files go here
- `Makefile`: Used to locally run unit tests, can be used for other functionalities as well
- `.github`: Contains the GitHub Workflows that run on every push and pull request
- `.git`: Contains GitHub Hooks for commit messages

###### Conventions and Rules to Follow

- Every commit should be linked with at-least one issue. Hence, every commit should have the GitHub
Issues that it belongs to. For example, if issue is `#100`, your commit should have `topic/#100`
mentioned in an independent line. Note that there is a checker.

Correct commit message

```text
Writing Unit Test for black_litterman.py

topic/#100

- Code coverage 80%.
```

Incorrect commit message

```text
Writing Unit Test for black_litterman.py
```

```text
Writing Unit Test for black_litterman.py topic/#100
```

```text
Writing Unit Test for black_litterman.py

topic/#100 - Code coverage 80%.
```

```text
Writing Unit Test for black_litterman.py

topic/100 

- Code coverage 80%.
```

```text
Writing Unit Test for black_litterman.py

#100 

- Code coverage 80%.
```

- For convention’s sake, name your branches `topic/<issue_number>`. For example: Issue `#100` should 
be worked on `topic/100`. There's no checker for branches though.
- Try to make commits as descriptive as possible.
- Changes to mainline can only be made through PRs. Please make the PR descriptions descriptive
  (preferably list of commit descriptions)
- When a PR is ready to be reviewed, please add `Ready for Review` label from the `Label` section
and then add `algo-trading-team` as reviewers.
- When a PR is ready to be merged, please add `Ready for Merge` label from the `Label` section.

###### Running Unit Tests Locally

- Running this command will run all the unit tests, with the source code being present at `src/`

```bash
make
```

- To see unit test writing convention, please refer to [Python Sample Test File](uwqsc_algorithmic_trading/tests/sample_test.py)

###### Running GitHub Workflows Locally

This requires you to have Docker installed. Install Act from https://nektosact.com/introduction.html

A successful act run looks like:
```bash
> cd ~/<algorithmic-trading-root>
> act
...
[Pylint/build            ]   ✅  Success - Main Analysing the code with pylint
[Pylint/build            ] ⭐ Run Post Set up Python 3.9
[Pylint/build            ]   🐳  docker exec cmd=[/opt/acttoolcache/node/18.20.5/arm64/bin/node /var/run/act/actions/actions-setup-python@v3/dist/cache-save/index.js] user= workdir=
[Pylint/build            ]   ✅  Success - Post Set up Python 3.9
[Pylint/build            ] Cleaning up container for job build
[Pylint/build            ] 🏁  Job succeeded
>
```