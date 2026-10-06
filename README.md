# Educate! Senior QA Engineer Assessment

## Part 3: CI/CD and E2E tooling

See [the framework comparison and merge-gate setup](docs/part3-ci-and-e2e.md).
The [GitHub Actions workflow](.github/workflows/test.yml) runs the API suite on
pull requests to `main` and uploads HTML/JUnit reports. Configure
**Attendance API quality gate** as a required status check to block merging on
test failures; the workflow alone does not enforce branch protection.

## Part 2: Attendance API testing

Python and pytest fit the team's existing Python familiarity. Requests sends real
HTTP POST requests to a local mock at `/api/v1/attendance`. No external service,
credentials, or manual server startup is required.

### Run locally

From this directory, with Python 3.10 or newer, follow these steps in order.

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate` instead. Activation applies to
your current terminal; repeat the activation command when opening a new one.

2. Before installing or running anything, confirm `.gitignore` contains the
following entries (this project already includes them):

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
reports/
.DS_Store
.coverage
.coverage.*
htmlcov/
.env
.env.*
!.env.example
```

These keep virtual environments, caches, reports, coverage output, macOS metadata,
and local environment secrets out of the repository. Keep source files, tests,
`pytest.ini`, `requirements.txt`, and this README in Git.

3. Install the test dependencies inside the active environment:

```bash
python -m pip install -r requirements.txt
```

4. Run the test suite:

```bash
python -m pytest -q
```

### HTML test report

Run `python -m pytest -v` for individual case names.

Every run also creates a self-contained HTML report at
`reports/test-report.html`, including test names, results, durations, and failure
details. Each run replaces the previous report. Generated reports are ignored by
Git; the HTML file can be shared separately.

HTML reporting is enabled in `pytest.ini` and `pytest-html` is included in
`requirements.txt`, so no extra reporting command is needed. The report reflects
the latest run, including any selected subset of tests. Run the full suite before
sharing it with reviewers.

On macOS, open it with:

```bash
open reports/test-report.html
```

After pulling changes to this project, run
`python -m pip install -r requirements.txt` to install the reporting dependency.

### Contract and assumptions

- The fixture reproduces the assessment's sample payload: `mentor_id`,
  `bootcamp_id`, `session_date`, and a `participants` array containing
  `participant_id` and `status`.
- A valid request returns HTTP 201 and JSON containing `success: true`, the
  submitted attendance data, `recorded_count`, `present_count`, and `absent_count`.
- Required identifiers are non-empty strings. Dates are valid `YYYY-MM-DD` dates.
- Only `PRESENT` and `ABSENT` are accepted, with case-sensitive validation.
- Empty participant lists and repeated participant IDs within one request return
  HTTP 400. The brief leaves their exact behavior open; these are explicit
  assumptions to confirm with the Product Owner/API owner.
- HTTP 400 responses contain `success: false` and an error field and message.
  The response schema is assumed because none is supplied. Validation returns
  the first error; collecting all errors is not a requirement in the brief.
- The sample has no age field, so age validation belongs to registration and is
  not added to the attendance contract.

### Coverage

| Category | Checks |
| --- | --- |
| Happy path | Sample request returns 201, JSON success, both attendance records and the correct count |
| Validation | Missing required fields, invalid mentor ID, invalid status, missing participant ID and invalid dates return 400 |
| Edge cases | Empty participants, duplicate IDs, invalid structures, single/500-participant batches, leap day, and all-or-nothing rejection |
| HTTP contract | Malformed/non-object JSON returns 400; GET/PUT/PATCH/DELETE return 405 with Allow: POST |

### Design and limits

`support/client.py` owns HTTP calls and the request timeout.
`support/validation.py` defines validation without inferred ID-prefix rules.
`support/mock_api.py` serves the contract and stores accepted batches in memory.
`support/payloads.py` builds fresh sample and boundary payloads.
`tests/conftest.py` starts a server on an available loopback port, creates fresh
payloads, and closes the server and clients after testing. Tests assert HTTP
status, JSON content type, success/error shape and returned data independently
of the mock's validation helper.

This suite demonstrates testing against an assumed mock contract. Passing it
does **not** prove Educate!'s actual endpoint behaves correctly. The mock stores accepted batches in memory only; it does not verify durable
database persistence, authenticate mentors, check participant existence, or
model replay/idempotency behavior. A storage test verifies that an invalid second
participant, duplicate IDs, or an empty list leave existing records unchanged. Against a real test environment, I would confirm
the contract, add authorization and persistence checks, and test replayed
requests and all-or-nothing handling of invalid batches.


### Selecting tests and using a test environment

```bash
python -m pytest -m edge_case -v
python -m pytest -k duplicate -v
```

After confirming the assumed request/response contract matches an authorized,
disposable test environment, the same HTTP tests can be directed there:

```bash
ATTENDANCE_API_URL=https://staging.example.org python -m pytest -q
```

This sends attendance submissions to that environment. The three tests requiring
access to the mock's internal store skip; they need a real read API or database
check to verify persistence. Authentication is not implemented yet.
Localhost requests bypass environment proxy settings; remote requests preserve
them. No external environment is used by default.

The 500-participant case checks correctness at that size, not performance or a
confirmed maximum batch size. Counts, HTTP 405 behavior, and in-memory atomicity
are additional mock-contract assumptions to confirm with the API owner.
