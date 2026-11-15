# Review presentation milestone

Make the existing research results easier to demonstrate on 16 November. Preserve
all original CTs, predictions, numeric results and accepted output folders.

## Design and risks

Use semantic offline HTML, embedded local CSS/JavaScript and native browser
controls. No service, authentication, dependency or GPU work. Lead with a case
summary and interactive native viewer; put technical metadata in an expandable
section. Navigation remains usable without JavaScript. Keep research status and
uncalibrated-score meaning visible in presentation and print views.

An experiment selector may compare only the eight verified occlusion results.
Show fixed-target mean scores and signed differences, never reinterpret these as
patient risk or make a synthetic explanation. Absent evidence stays unavailable.
Guard DOM input bounds and avoid interpolating case strings into executable code.

## Tasks and checks

- [x] Report cards, navigation, presentation mode and print styles.
- [x] Saved-experiment interaction; check selected scores/sign and invalid input.
- [x] Landing page with clear pipeline/case links and evidence availability.
- [x] Rebuild a fresh offline ZIP; preserve numeric JSON and original PNG bytes.
- [ ] Python/Node/lint checks, local links/ZIP integrity, rendered report review.
- [ ] Current progress, final review script, source commit/push verification.

Clinical validation, diagnosis references and reviewed subregion labels remain
lead-dependent and are not completed by this presentation milestone.

244 Python and 11 Node checks passed; scoped lint/format, dependency, local links
and ZIP integrity checked. Native browser/print review remains pending because
Computer Use could not confidently verify the current URL and stopped. No native
polished-layout acceptance is claimed. A separate nine-slide PowerPoint was
created, finalized and rendered/visually inspected for the review; see PROGRESS.md.
