# HANDOFF TEMPLATE
**Reminder:** ***Claims with no update for seven days may be released after a maintainer check-in! There will be no automated reminders or reassignment, so please provide regular updates! :)***

- **Issue Link:** *insert link*
- **PR Link *(if needed)*:** *insert link*
- **Branch Link *(if needed)*:** *insert link*
- **Last Reviewed SHA:** *insert commit SHA*

## WORK ACCOMPLISHED
### Implemented Work
- List the work that has been completed
- Include relevant commits or documentation as evidence

### Checks Performed
- List checks you have actually performed
- Include the results of those checks
- Clearly identify anything that has not been tested

### Work Remaining
- List incomplete tasks or functionality that still needs to be implemented
- Explain what remains to be done

### Maintainer Review / CI Status
- Document whether the maintainer has reviewed the work
- Record the CI status and any pending approvals
- Do not imply that work has passed review or CI without evidence

## REPRODUCTION INSTRUCTIONS 
- **Environment**: *Describe the environment or setup required*
- **Steps**: *Provide exact steps or commands to reproduce the current state*
- **Expected Result**: *Describe what should happen*
- **Actual Result**: *Describe what currently happens*

## REMAINING BLOCKERS
- *List any outstanding issues, errors, or dependencies*
- *Explain what is getting you stuck and, if you can, what you think a potential approach could be*

## RELEASE REQUEST
- *If you are unable to continue working on the issue, explicitly state that you are requesting to have your claim released so another contributor can take over*

# *TEST HANDOFF EXAMPLE*
- **Issue:** [#453](https://github.com/HafidIdrissi/Time-Tracker/issues/453)
- **PR:** [#932](https://github.com/HafidIdrissi/Time-Tracker/pull/932)
- **Branch:** `feature/fix-activity-tracking`
- **Last Reviewed SHA:** `abc1234`

## WORK ACCOMPLISHED
### Implemented Work
- Updated the activity tracking logic to handle missing application names
- Added a validation check to prevent incomplete activity records from being saved
- Added a unit test covering the new validation behaviour

### Checks Performed
- Reviewed the new unit test and its assertions
- The unit test has not yet been executed
- Existing activity tracking behaviour has not yet been regression-tested

### Work Remaining
- Run the new unit test
- Verify that the validation works correctly with older activity records
- Update the relevant documentation

### Maintainer Review / CI Status
- Awaiting maintainer review
- [Workflow](https://github.com/HafidIdrissi/Time-Tracker/actions/runs/41167137614) is awaiting maintainer approval to run
- A maintainer has not yet reviewed the new validation
- Compatibility with older activity records has not yet been verified

## REPRODUCTION INSTRUCTIONS
- **Environment:** Windows 11, Python 3.13
- **Steps:**
  1. *Launch the application*
  2. *Generate activity records with missing application names*
  3. *Run the new unit test*
- **Expected Result:** Records with missing application names should be handled by the new validation logic
- **Actual Result:** The expected behaviour has not yet been confirmed because the new unit test has not been executed

## REMAINING BLOCKERS
- Unable to continue work due to personal scheduling constraints :(

## RELEASE REQUEST
I am no longer able to actively work on this issue.
Could a maintainer please release my claim so another contributor
can pick it up? Thank you!

# *DOC HANDOFF EXAMPLE*
- **Issue:** [#454](https://github.com/HafidIdrissi/Time-Tracker/issues/454)
- **PR:** [#933](https://github.com/HafidIdrissi/Time-Tracker/pull/933)
- **Branch:** `docs/update-installation-guide`
- **Last Reviewed SHA:** `def5678`

## WORK ACCOMPLISHED
### Implemented Work
- Updated the installation guide with clearer setup instructions
- Added instructions for configuring the application
- Added examples of common configuration options

### Checks Performed
- Previewed the Markdown document and confirmed the formatting displays correctly
- Checked that the documentation links work
- Reviewed the instructions for clarity and consistency

### Work Remaining
- Add a troubleshooting section for common installation errors
- Verify the instructions on a fresh installation
- Review the remaining documentation for consistency with the updated guide

### Maintainer Review / CI Status
- Awaiting maintainer review
- Documentation changes have not yet been reviewed by a maintainer
- No CI results are available yet

## REMAINING BLOCKERS
- Unable to continue work due to personal scheduling constraints :(

## RELEASE REQUEST
I am no longer able to actively work on this issue.
Could a maintainer please release my claim so another contributor
can pick it up? Thank you!
