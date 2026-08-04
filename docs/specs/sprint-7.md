# Sprint 07: Final Delivery, CI, and Packaging

MMC Watershed Data already satisfies the core functional goals of collecting,
validating, processing, analyzing, and presenting real rainfall observations.
This sprint closes the minimum course-project requirements by auditing those
guarantees, running the offline checks automatically in GitHub Actions, proving
that the project builds as an installable package, and producing the exact
wheel and source archive required for submission.

This sprint is independent of the optional Thiessen analysis described in
Sprint 6. Completing Sprint 7 must not require implementing Thiessen polygons,
areal rainfall, or any other Sprint 6 feature.

## Context

The project already provides:

- real Auburn and Opelika API integrations;
- raw JSON evidence and raw CSV inspection extracts;
- processed station CSV outputs;
- public endpoints that do not require an API key;
- a repeatable `mmc` command;
- Pydantic validation and clear validation failures;
- offline fixtures, mocked API boundaries, and passing tests;
- a Streamlit dashboard and reproducible Quarto PDF report;
- `uv` project metadata, a custom build backend, and ignored `dist/` output.

The repository does not yet contain a GitHub Actions workflow. The documented
build command is currently `uv build`, while the final submission specifically
requires `uv build --no-sources`. A successful local build alone is not enough:
the final wheel and source archive must also pass clean-environment checks.

## Objective

Produce a final, auditable submission build in which:

1. every push runs the offline quality checks in GitHub Actions;
2. package metadata has one consistent version and dependency definition;
3. `uv build --no-sources` creates one wheel and one source archive;
4. the wheel can be installed and its `mmc` command can run in a clean
   environment;
5. the source archive can build the same wheel independently of the working
   tree; and
6. the exact two verified `dist/` files are ready for submission.

## Minimum-Requirement Audit

Treat the course checklist as a submission gate. For each requirement, preserve
or add executable evidence rather than relying only on prose.

### Real API data

- Keep Auburn and Opelika network access isolated at the existing API
  boundaries.
- Preserve one realistic manual final check using the public APIs and a
  short date range.
- Do not call either live API from unit tests or GitHub Actions.
- Document that API availability is external and that transient provider
  failures do not invalidate offline tests.

### Raw and processed evidence

- Confirm every successful station collection writes raw JSON before or
  alongside processing.
- Confirm raw CSV remains an inspection extract and processed CSV remains the
  stable downstream schema.
- Confirm validation failures preserve raw response evidence whenever a
  response was received.
- Keep generated `data/` ignored by Git; runtime evidence is not required to be
  committed to prove that the command creates it.
- Add or preserve tests that assert expected raw and processed paths and file
  contents using temporary directories.

### Secrets and repository hygiene

- Keep `.env`, `.venv/`, `data/`, `logs/`, `dist/`, `.coverage`, `htmlcov/`,
  `.vscode/`, and notebook checkpoints out of Git.
- Do not add an unnecessary `.env.example` or API-key instruction because the
  current endpoints are public.
- Verify tracked files do not contain a real credential, token, private URL,
  generated coverage database, checkpoint, or run-specific data output.
- GitHub Actions must use read-only repository permissions.
- Do not echo GitHub tokens, environment details containing secrets, raw API
  payloads, or authorization headers in CI logs.

### Repeatable command and validation

- Preserve the existing command contract:

```bash
uv run mmc --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

- Verify `mmc --help` and `mmc --version` after installation from the wheel.
- Keep clear failures for malformed dates, reversed date ranges, invalid API
  response fields, malformed timestamps, and invalid rainfall values.
- Keep Pydantic at the external data boundary rather than validating only
  after unsafe processing.
- Ensure command failures use concise user-facing messages while detailed
  diagnostics remain available through secure logging options.

### Offline tests and presentation

- Keep fixtures small, deterministic, and free of secrets.
- Mock network calls at the request boundary.
- Cover controlled success and failure behavior for Auburn, Opelika,
  validation, storage, shared workflow, dashboard analysis, and report input.
- Preserve the Streamlit dashboard as the interactive audience-facing result.
- Preserve the authoritative Quarto `.qmd` and its inspected PDF as the
  detailed reproducible artifact.
- Do not make CI depend on a browser, live API, or interactive dashboard
  session.

## GitHub Actions CI

Add an authoritative workflow at:

```text
.github/workflows/ci.yml
```

### Triggers

Run CI on:

- every push to every maintained branch, including `main`;
- every pull request targeting `main`; and
- optional manual dispatch for final package preparation.

The required evidence is that tests run automatically on push. Pull-request
and manual triggers add review and recovery paths but do not replace the push
trigger.

### Environment

- Use a current Ubuntu GitHub-hosted runner.
- Check out the exact commit under test.
- Install the Python version supported by `pyproject.toml`.
- Install `uv` through the maintained official setup action or another pinned,
  documented method.
- Restore dependencies with the lockfile in frozen/locked mode so CI cannot
  silently rewrite `uv.lock`.
- Use dependency caching only when it does not hide lockfile or build errors.
- Set workflow permissions to `contents: read` for the CI workflow.

### Required CI commands

The CI workflow must run the repository's documented checks from a clean
checkout:

```bash
uv sync --locked
uv run python -m pytest
uv run coverage run --source=mmc_watershed_data -m pytest
uv run coverage report --show-missing
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv build --no-sources
```

Avoid running the same full test suite twice if coverage can provide the one
authoritative test execution. The implemented workflow may combine the pytest
and coverage commands, but the logs must clearly show the tests, result, and
coverage report.

Establish and document a realistic coverage threshold after measuring the
current project. The submission gate should not reward a high percentage obtained
by omitting difficult core modules. API parsing, Pydantic validation, storage,
workflow orchestration, and pure analysis logic require direct success and
failure coverage. Dashboard rendering glue may be treated differently from
core logic when justified in documentation.

### CI failure behavior

- Any failed test, format check, lint check, type check, lockfile check, or
  package build must fail the workflow.
- CI must not retry failing tests by calling the live API.
- Failure logs must identify the command and actionable error.
- The final submitted commit must have a successful CI run on GitHub.

Quarto rendering may remain a documented local final check because its PDF
engine is external and substantially heavier than the Python test environment.
The committed PDF must still be rendered and visually inspected before submission.

## Package Metadata and Build Quality

The package is part of the submitted evidence, not merely an archive of source
files. Audit the wheel and source distribution as user-installable artifacts.

### Single source of version and metadata

- Select the final project version before building artifacts.
- Keep the same version in `pyproject.toml`, package `__version__`, `uv.lock`,
  README, changelog, wheel metadata, and source-archive name.
- Make the custom build backend derive project name, version, description, and
  runtime dependencies from `pyproject.toml` rather than maintaining a second
  conflicting dependency list.
- Ensure the project description reflects the current multi-city CLI,
  dashboard, validation, and reporting scope rather than the original
  single-station prototype.
- Verify the package declares every runtime dependency needed by installed
  CLI and dashboard code and excludes development-only tools from runtime
  requirements.

### Wheel contents

The wheel must contain:

- the complete `mmc_watershed_data` package;
- `mmc` console-script metadata;
- correct name, version, Python requirement, and runtime dependencies;
- license metadata and the standard license text where packaging conventions
  require it; and
- any runtime asset required for installed functionality, or a documented and
  tested external-asset lookup contract.

Do not rely on `sitecustomize.py`, the repository root, or an editable install
for normal wheel imports. A clean wheel installation must be able to run:

```bash
mmc --version
mmc --help
```

### Source archive contents

The source archive must contain enough tracked material to rebuild the wheel
without reading files from the original checkout. At minimum, include:

- `pyproject.toml` and the custom build backend;
- complete package source;
- README and LICENSE;
- package/runtime assets needed by installed behavior; and
- any additional metadata required by the build backend.

Tests, fixtures, documentation, and the report source should be included when
they are part of the intended reproducible source distribution. Generated data,
logs, virtual environments, coverage files, temporary files, and previous
`dist/` artifacts must not be included.

### Required build command

From a clean project checkout, run exactly:

```bash
uv build --no-sources
```

The command must create exactly the current-version artifacts:

```text
dist/mmc_watershed_data-X.Y.Z-py3-none-any.whl
dist/mmc-watershed-data-X.Y.Z.tar.gz
```

Older local files may remain ignored during development, but final verification
must select only the two files matching the exact project version. Prefer
cleaning or using an empty `dist/` before the final build so stale artifacts
cannot be mistaken for submission files.

`--no-sources` is mandatory for the final build even if the project does not
currently define alternate `tool.uv.sources`. This proves the package resolves
from normal published requirements rather than local source overrides.

## Clean-Environment Package Verification

Add an automated script, test, or documented package check that verifies the
built artifacts outside the development environment.

### Wheel verification

1. Create a temporary virtual environment that is not the project `.venv`.
2. Install the exact wheel from `dist/` without an editable source path.
3. Run `mmc --version` and compare it with the project version.
4. Run `mmc --help` and verify the date, logging, and output guidance.
5. Import the package from outside the repository root.
6. Confirm package metadata lists the expected runtime dependencies.

Do not use the live rainfall APIs for this installation smoke test.

### Source-archive verification

1. Extract the exact `.tar.gz` into a temporary directory.
2. Confirm no ignored/generated files are present.
3. Run `uv build --no-sources` from the extracted source tree.
4. Confirm the rebuilt wheel has the same project name and version.
5. Install or inspect the rebuilt wheel sufficiently to prove the archive is
   self-contained.

Tests that inspect wheel and source-archive member names should normalize path
separators so they pass on Windows, macOS, Linux, and GitHub Actions.

## Packaging Documentation

Update `README.md` with a concise **Package Evidence** section that
documents:

- the exact `uv build --no-sources` command;
- the two expected files in `dist/`;
- the clean wheel smoke-test command or package-check script;
- the fact that `dist/` remains generated and ignored rather than committed;
- how to verify the wheel and source archive before submission.

Add a durable packaging checklist under `docs/`, such as:

```text
docs/package-checklist.md
```

The checklist should be reusable for future versions, not tied only to one
temporary terminal session. Link it from `docs/index.md` and the README.

Update `AGENTS.md` so the authoritative package check uses
`uv build --no-sources`. Do not turn `AGENTS.md` into a submission transcript.

## Tests

Add or update offline tests for:

- `mmc --help` and `mmc --version` matching package metadata;
- Pydantic validation success and controlled bad external data;
- raw evidence and processed output creation in temporary directories;
- API success, HTTP failure, retry, malformed response, and empty response
  using mocks;
- repository hygiene expectations for `.coverage`, notebook checkpoints,
  `.env`, generated data, and `dist/`;
- CI workflow presence and required push trigger;
- CI use of locked dependency restoration and offline tests;
- CI use of `uv build --no-sources`;
- wheel member names, console entry point, metadata, dependencies, and license;
- source-archive completeness and absence of generated artifacts;
- clean wheel installation or an equivalent isolated smoke test; and
- documentation links to CI, package evidence, package checklist, report, and
  license.

Tests that verify CI and packaging configuration should assert meaningful
contracts without depending on incidental YAML formatting or member order.

## Manual Final Verification

Run locally from the final submitted commit:

```bash
uv sync --locked
uv run coverage run --source=mmc_watershed_data -m pytest
uv run coverage report --show-missing
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv build --no-sources
quarto render reports/mmc-rainfall-report.qmd --to pdf
```

Also verify:

```bash
uv run mmc --version
uv run mmc --help
uv run streamlit run src/mmc_watershed_data/dashboard.py
```

Perform one short live API collection manually and confirm raw JSON, raw CSV,
processed CSV, dashboard loading, and clear station failures. Do not add the
generated `data/` files to Git.

Inspect the rendered PDF and dashboard visually. Review the successful GitHub
Actions run in the GitHub UI rather than assuming a workflow file guarantees a
passing hosted run.

## Acceptance Criteria

- Real Auburn and Opelika data can be collected through the public APIs.
- Raw JSON evidence and processed CSV outputs are created and tested.
- Secrets and generated artifacts remain outside Git.
- `mmc` remains a repeatable, documented command.
- External responses cross Pydantic validation and bad input fails clearly.
- Offline tests use fixtures and mocks and provide appropriate coverage of
  core logic.
- GitHub Actions runs the offline tests automatically on every push.
- The final submitted commit has a successful GitHub Actions run.
- The Streamlit dashboard and Quarto PDF remain current audience-facing
  artifacts.
- `uv build --no-sources` succeeds from a clean checkout.
- Exactly one current-version wheel and one current-version custom source
  archive are produced.
- The wheel installs outside the development environment and runs
  `mmc --version` and `mmc --help`.
- The source archive independently rebuilds the wheel.
- Version, package metadata, changelog, and artifact names agree.
- Both `uv build --no-sources` artifacts pass clean-environment checks.
- README, package checklist, AGENTS.md, data dictionary, report, and license
  remain linked and current.

## Out Of Scope

- Implementing Sprint 6 Thiessen polygons or areal rainfall analysis.
- Adding a new API, city, station network, or rainfall transformation.
- Calling live APIs from GitHub Actions.
- Committing generated `data/`, `dist/`, logs, coverage databases, or virtual
  environments.
- Cloud deployment of the Streamlit dashboard.
- Automated hydrologic simulation or model calibration.
- Publishing the package to PyPI unless separately required.
- Rewriting completed sprint specifications.
