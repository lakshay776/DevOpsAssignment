# Mini Project: CI Pipeline for a Python App

The course's `mini-project` folder is empty. Its only brief is the line in the session README:
*"Build a complete CI pipeline for a Python app."* This folder is that pipeline, built from the
pieces taught in modules 04-09.

```text
mini-project/
├── .github/workflows/ci.yml   # the pipeline
├── app/calculator.py          # the app: add, subtract, multiply, divide
├── tests/test_calculator.py   # 5 pytest tests
├── requirements.txt           # pytest, pytest-cov, flake8 (pinned)
├── build.sh                   # packages app/ into build/ with build-info.txt
└── .gitignore
```

## Pipeline

```text
          ┌── Test (pytest + coverage, uploads test-results) ──┐
Lint ─────┤                                                     ├── Build (build.sh, uploads calculator-build)
          └── Security Check (no .env / *.pem / *.key) ────────┘
```

- Triggers: `push` and `pull_request` to `main`, plus `workflow_dispatch` for manual runs.
- `Test` and `Security Check` both have `needs: lint`, so they run in parallel after lint passes.
- `Build` has `needs: [test, security-check]`, so a failing test means nothing gets built.
- Test results are uploaded with `if: always()`, so the report exists even when tests fail.

## Run locally

```bash
pip install -r requirements.txt
flake8 app/ tests/
python -m pytest -v tests/
./build.sh
python -m app.calculator
```

## Run the workflow locally with act

```bash
act push --artifact-server-path /tmp/artifacts
act workflow_dispatch --artifact-server-path /tmp/artifacts
```

The workflow only triggers on GitHub when `.github/workflows/ci.yml` sits at the **root** of a
repository. Copy this folder into a repository of its own to use it there.
