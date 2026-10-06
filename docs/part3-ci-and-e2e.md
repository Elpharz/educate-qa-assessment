# Part 3: CI/CD Pipeline & E2E Tooling Selection

## 1. Framework trade-off analysis

Playwright for Python and Selenium with pytest both let a Python-familiar team
adopt browser automation without introducing another test language. Selenium is
a strong option when an existing WebDriver suite or Grid infrastructure can be
reused; its explicit wait APIs support dynamic pages, but the team must maintain
those synchronization decisions. Playwright integrates with pytest and provides
automatic actionability checks, isolated browser contexts, and device emulation.
For Educate!'s web and mobile-responsive applications, these features would help
reduce custom setup and timing-related maintenance. I would use role-based
locators and reusable page objects in either framework. Execution speed should
be measured on representative journeys rather than assumed from framework choice.

I recommend **Playwright for Python** as the initial E2E choice, alongside the
pytest/Requests attendance API suite. Start with a small smoke suite covering
registration, offline-to-online synchronization, and attendance submission, then
expand browser coverage according to field usage. Validate the choice through a
short spike comparing CI duration, repeat-run reliability, and team maintenance
effort against Selenium. Mobile emulation checks responsive behavior but does
not establish compatibility with actual low-end phones, SMS delivery, or USSD;
those need representative-device checks and separate channel integration tests.
This assessment implements API automation only; adding browser tests requires
the web application and a test environment.

References: [Playwright pytest integration](https://playwright.dev/python/docs/test-runners),
[Playwright automatic waiting](https://playwright.dev/python/docs/actionability),
[device emulation](https://playwright.dev/python/docs/emulation), and
[Selenium waiting strategies](https://www.selenium.dev/documentation/webdriver/waits/).

## 2. CI/CD configuration and quality gate

The configuration is in [test.yml](../.github/workflows/test.yml). It runs on
every pull request targeting `main`, pushes to `main`, and manual dispatch.
A GitHub-hosted Ubuntu runner installs Python 3.12 and the test dependencies,
then runs the full local-mock suite. Pytest returns a non-zero exit code for a
failed test or test error, causing the job to fail. No `continue-on-error` or
error suppression is used. HTML and JUnit reports are uploaded even when tests
fail, when those files are available. Reports are retained for 14 days.

### Enforcing the merge gate

A failed workflow alone does not prevent merging. Configure protection for
`main` in the repository's **Settings > Branches**, or an equivalent branch
ruleset:

1. Require a pull request before merging.
2. Require status checks to pass before merging.
3. Select **Attendance API quality gate** as a required check after its first run.
4. Require branches to be up to date before merging.
5. Disable bypasses so the same gate applies to administrators where supported.

With that protection enabled, a failing required check blocks merging. This is a
repository setting, not something the YAML file can enable by itself. If a merge
queue is later enabled, add the `merge_group` trigger so the required check also
runs for queued merges.

### Review and validation

Open **Actions > Attendance API Tests**, select a run, and download
**attendance-test-reports** to inspect the HTML and JUnit results. Before relying
on the gate, create a temporary PR with a deliberately failing assertion and
confirm both the failed check and blocked merge; revert the assertion and confirm
the check passes. 

This workflow tests the mock contract. It is not a deployment pipeline or proof
of production readiness; real API integration and browser E2E checks would be
added once the corresponding environments are available.

References: [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
and [required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).
