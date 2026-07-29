# Sprint 03: Test Reliability, Validation, and Logging

MMC Watershed Data is a `uv`-managed Python command-line tool for collecting
rainfall data from Auburn and Opelika. This sprint strengthens the internal
boundaries of the project so that external API data can be tested offline,
validated before analysis, and diagnosed without making normal output noisy.

## Context

The current project already separates the Auburn and Opelika API workflows and
saves raw JSON, raw CSV, and processed CSV outputs. The next step is to make
the collection and processing behavior easier to trust and reuse. The command
line tool and the future Streamlit dashboard should share the same validation,
transformation, and request workflow.

## User Features: What

- A developer can run the complete test suite without calling either live API.
- A developer can use small JSON fixtures that represent valid and invalid API responses.
- A developer can mock Auburn and Opelika network calls and assert request details.
- The application validates external response fields before using them for analysis.
- Invalid external data produces a clear domain-level error instead of an obscure traceback.
- Raw evidence is saved before processed-data validation fails whenever possible.
- A normal command run remains readable and does not print diagnostic logs.
- A developer can enable verbose operational logs for troubleshooting.
- A developer can write detailed logs to a file without exposing secrets.
- The future dashboard can reuse the same request and processing workflow as `mmc`.
- The README explains the new testing, validation, logging, and shared-workflow features.

## Implementation Plan: How

- Keep stable JSON response examples under `tests/fixtures/`.
- Add at least one invalid fixture for each important response shape or transformation rule.
- Load fixture files from tests instead of duplicating large payloads inside test functions.
- Keep all network calls behind the existing API boundary modules.
- Use `unittest.mock` and `patch` or `monkeypatch` to replace network functions in tests.
- Assert URLs, query parameters, request bodies, station IDs, and selected date windows.
- Do not use live network access in unit tests.
- Add Pydantic models for the external fields consumed by the project.
- Validate Auburn response structure, timestamps, and rainfall values before conversion.
- Validate Opelika response structure, `CreatedDT`, and `RainToday` before cumulative-to-interval conversion.
- Keep internal processed records separate from external API models.
- Convert validation-library errors into small project-specific exceptions with useful field locations.
- Add a shared workflow layer that represents a date request and its collected station results.
- Keep raw writing, processed writing, and API access in separate modules.
- Add module-level loggers and a package `NullHandler` so importing the package is quiet.
- Support optional `--verbose` terminal logging and optional `--log-file` detailed logging.
- Use `INFO` for request and output milestones, `DEBUG` for diagnostic details, and `WARNING` for recoverable failures.
- Never log API keys or other credentials.
- Update `README.md` with the Sprint 3 features, test commands, fixture and mock strategy,
  Pydantic validation behavior, and logging options.

## Fixture and Mock Expectations

The tests should make the boundary between evidence and simulation clear:

- A fixture is saved example data used as input to parsing and processing tests.
- A mock replaces a side effect such as an HTTP request, retry, or file-related dependency.
- A test may use both: a fixture supplies the response body while a mock supplies it through the API boundary.
- Output tests should use temporary directories and must not write to the project's real `data/` folders.

## Pydantic Expectations

Pydantic should validate only the fields the application needs. It should not
be used as a replacement for the raw evidence. The expected flow is:

```text
external JSON
    -> raw evidence
    -> Pydantic validation
    -> trusted internal records
    -> rainfall conversion and analysis
```

The validation models should preserve the source-specific rules:

- Auburn timestamps arrive as epoch milliseconds and rainfall values are station rain amounts.
- Opelika timestamps arrive in the source date/time format and `RainToday` is cumulative.
- A negative interval caused by a rainfall-counter reset is handled by the documented Opelika rule.

## Tests

Add or update tests for:

- valid Auburn fixture loading and transformation;
- valid Opelika fixture loading and cumulative-rain conversion;
- malformed Auburn and Opelika payloads;
- invalid timestamps and numeric values;
- mocked HTTP success, HTTP failure, connection failure, and retry behavior;
- exact request construction for both APIs;
- raw JSON and CSV evidence writing;
- processed CSV writing;
- date-range validation in the shared workflow;
- quiet logging by default;
- `--verbose` terminal logging;
- `--log-file` debug logging and handler cleanup;
- console and file logs do not contain API keys or other credentials.

## Verification

```bash
uv run python -m unittest discover -s tests
uv build
```

## Documentation

Update `README.md` to document:

- the purpose of fixtures and mocks in the test suite;
- the validation boundary and the source-specific Pydantic rules;
- the available logging options, including `--verbose` and `--log-file`;
- the shared workflow used by the CLI and future dashboard;
- the commands needed to run tests and build the project.

## Out Of Scope

- Streamlit pages or browser interaction.
- Map rendering or KMZ parsing.
- New data sources or new cities.
- Database storage.
- Changing the existing station processing rules without a documented reason.
